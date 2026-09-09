import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import __version__
from .critique import (
    Critique,
    apply_responses,
    extract_revision,
    numbered_points,
    parse_critique,
)
from .governance import REQUIRED_SECTIONS, Review, flagged_roles, review_text
from .llm import (
    LLMClient,
    ProviderConfigError,
    build_critic_prompt,
    build_prompt,
    build_response_prompt,
    get_llm,
)
from .roles import SPECIALISTS, get_role
from .router import Plan, Router
from .storage import (
    StorageError,
    append_log,
    artifact_root,
    clear_lock,
    find_run,
    lock_holder_alive,
    new_run_id,
    now_iso,
    read_manifest,
    run_dir,
    sha256_text,
    validate_run_id,
    write_lock,
    write_manifest,
)

log = logging.getLogger(__name__)
# Each specialist sees at most this many characters of every predecessor's artifact.
CONTEXT_CHARS = 600
# The task is echoed into the manifest and the append-only log. Keep a single log line well
# inside PIPE_BUF so concurrent appends cannot splice into an unparseable record.
MAX_TASK_CHARS = 2000


@dataclass
class ArtifactRecord:
    role: str
    file: str | None
    review: dict | None
    error: str | None = None
    sha256: str | None = None
    critique: dict | None = None
    revised: bool = False
    # Findings the artifact bytes cannot show, so the gate must not try to re-derive them.
    process_flags: list[str] = field(default_factory=list)


@dataclass
class RunRecord:
    run_id: str
    task: str
    provider: str
    plan: dict
    artifacts: list[ArtifactRecord] = field(default_factory=list)
    status: str = "running"
    created_at: str = ""
    # Counts derived from the synthesis artifact's registers; None when no synthesis ran.
    synthesis: dict | None = None
    version: str = __version__

    @property
    def all_approved_by_governance(self) -> bool:
        return not flagged_roles([asdict(a) for a in self.artifacts])


def _excerpt(text: str) -> str:
    return text if len(text) <= CONTEXT_CHARS else text[:CONTEXT_CHARS] + " …"


CRITIC_ROLE = "qa_qc"
# No routing rule matched, so the plan is a guess rather than a decision. This is a fact about
# how the run was planned, not about the artifact's bytes, so it travels in process_flags — the
# same path truncation and dismissed critiques use. flagged_roles() iterates artifacts, so a
# plan-level field would never reach the gate; attaching it to the artifact the default plan
# produced is what makes a human's --force the only way past it.
DEFAULT_PLAN_FLAG = (
    "No routing rule matched; the default specialist was dispatched on a guess "
    "(check the task is aimed at the right seat)"
)


def critique_and_revise(
    role_key: str,
    task: str,
    context: str,
    artifact: str,
    llm: LLMClient,
    critic_key: str = CRITIC_ROLE,
) -> tuple[str, Review, Critique, list[str]]:
    """One round: a critic challenges the draft, the author answers every point and reissues.

    The critic never edits. The author owns the revision, so authorship and accountability stay
    together, and a rejected challenge has to carry a reason that a human can read.
    """
    role, critic = get_role(role_key), get_role(critic_key)
    c_system, c_prompt = build_critic_prompt(critic, role.title, task, artifact)
    critique = parse_critique(llm.generate(c_system, c_prompt, role=critic_key).text, critic_key)
    if not critique.points:
        # Nothing to answer: keep the draft and the review it already earned, truncation and all.
        return artifact, review_text(artifact), critique, []

    a_system, a_prompt = build_response_prompt(
        role, task, context, artifact, numbered_points(critique)
    )
    answer = llm.generate(a_system, a_prompt, role=role_key)
    apply_responses(critique, answer.text)
    revised = extract_revision(answer.text)
    final = revised or artifact
    # Only re-derive the review when the text actually changed; otherwise the draft keeps the
    # findings it already had, including truncation.
    flags = []
    if answer.truncated and revised:
        flags.append("Revision truncated at the token budget (raise LLM_MAX_TOKENS)")
    for point in critique.blocking_unresolved:
        flags.append(f"Unresolved blocking critique ({point.dimension}): {point.claim}")
    return final, review_text(final), critique, flags


def produce(
    role_key: str, task: str, llm: LLMClient, context: str = ""
) -> tuple[str, Review, list[str]]:
    """Returns the draft, a review derived purely from its bytes, and process findings.

    Keeping the review byte-pure is what lets the gate re-derive and verify it; anything the
    bytes cannot show (a truncated generation) travels separately.
    """
    role = get_role(role_key)
    if role_key not in SPECIALISTS:
        raise ValueError(f"'{role_key}' is a supervisor role and cannot be dispatched")
    system, prompt = build_prompt(role, task, context)
    completion = llm.generate(system, prompt, role=role_key)
    flags = []
    if completion.truncated:
        # Say what actually went wrong; the missing tail sections are a symptom of the cap.
        flags.append("Output truncated at the token budget (raise LLM_MAX_TOKENS)")
    return completion.text, review_text(completion.text), flags


SYNTHESIS_ROLE = "engagement_lead"
# The registers the Engagement Lead must carry inside Body. Absence and emptiness must never
# look the same, so an empty register is required to say "None." rather than be omitted.
SYNTHESIS_REGISTERS = ("Recommendation", "Decisions", "Disagreements", "Escalations")
# The registers live inside the outer envelope's plain "Body:" section, so the last register's
# body must stop at the next envelope label too — not just the next "##" heading — or it runs
# on through "Citations:"/"Risks:"/"Next Steps:" and silently absorbs their numbered lines.
_ENVELOPE_LABEL_RE = "|".join(re.escape(sec) for sec in REQUIRED_SECTIONS)
_REGISTER_RE = re.compile(
    r"^[ \t]*#{1,6}[ \t]*(?P<name>" + "|".join(SYNTHESIS_REGISTERS) + r")[ \t]*$"
    r"(?P<body>.*?)"
    r"(?=^[ \t]*#{1,6}[ \t]*\S|^[ \t]*(?:" + _ENVELOPE_LABEL_RE + r")[ \t]*:|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)


def parse_registers(text: str) -> dict[str, list[str]]:
    """Numbered entries under each register heading. An explicit 'None.' yields an empty list.

    Byte-derived and regex-only on purpose: the counts the CLI and the gate rely on must not
    require a model call to obtain, and must be reproducible from the artifact alone.
    """
    out: dict[str, list[str]] = {r.lower(): [] for r in SYNTHESIS_REGISTERS}
    for m in _REGISTER_RE.finditer(text):
        body = m.group("body")
        if re.search(r"^\s*none\.?\s*$", body, re.IGNORECASE | re.MULTILINE):
            continue
        out[m.group("name").lower()] = [
            line.strip() for line in re.findall(r"^[ \t]*\d+[.)][ \t]*(.+)$", body, re.MULTILINE)
        ]
    return out


def synthesize(
    task: str, artifacts: list[ArtifactRecord], llm: LLMClient, run_out: Path | None = None
) -> tuple[str, Review, list[str]]:
    """The Engagement Lead reads every successful artifact in full and integrates them.

    Deliberately does NOT call produce(): that function raises on any role outside SPECIALISTS,
    and the guard must keep holding so the router and the governance evaluator can never be
    dispatched as peers. The lead is a supervisor and reaches the model through its own path.
    """
    role = get_role(SYNTHESIS_ROLE)
    parts: list[str] = []
    for a in artifacts:
        if a.error or not a.file or run_out is None:
            continue
        body = (run_out / a.file).read_text(encoding="utf-8")
        head = f"[{get_role(a.role).title}] governance: {(a.review or {}).get('verdict', '?')}"
        if a.process_flags:
            head += f" | flags: {'; '.join(a.process_flags)}"
        unresolved = [
            p["claim"]
            for p in ((a.critique or {}).get("points") or [])
            if p.get("severity") == "blocking" and p.get("disposition") != "accepted"
        ]
        if unresolved:
            head += f" | UNRESOLVED BLOCKING CRITIQUE: {' / '.join(unresolved)}"
        parts.append(f"{head}\n{body}")

    missing = [a.role for a in artifacts if a.error]
    context = "\n\n---\n\n".join(parts)
    if missing:
        context += (
            "\n\n---\n\nSEATS THAT PRODUCED NOTHING (name this absence in your artifact): "
            + ", ".join(missing)
        )
    system, prompt = build_prompt(role, task, context)
    completion = llm.generate(system, prompt, role=SYNTHESIS_ROLE)
    flags = []
    if completion.truncated:
        flags.append("Output truncated at the token budget (raise LLM_MAX_TOKENS)")
    regs = parse_registers(completion.text)
    # An escalation is a question only the human can answer, so it must cost a human their
    # signature: it rides process_flags to flagged_roles() and forces --force plus a note.
    for esc in regs["escalations"]:
        flags.append(f"Escalated to the human: {esc}")
    return completion.text, review_text(completion.text), flags


def _do_synthesis(
    record: RunRecord,
    task: str,
    llm: LLMClient,
    out: Path,
    run_id: str,
    log_file: Path | None,
    critique: bool,
) -> None:
    """Attempt the Engagement Lead and record the outcome on `record`, success or failure.

    Shared by run() (first attempt, right after the specialist loop) and resynthesize()
    (a retry against artifacts already on disk). Never raises: a failed synthesis is recorded
    as an errored ArtifactRecord, exactly like a failed specialist, so it never costs the
    advisors' work that already succeeded.
    """
    if not any(not a.error for a in record.artifacts):
        append_log(
            {
                "event": "synthesis_skipped",
                "run_id": run_id,
                "reason": "no specialist produced an artifact to integrate",
            },
            log_file,
        )
        return
    try:
        s_text, s_review, s_flags = synthesize(task, record.artifacts, llm, out)
    except ProviderConfigError:
        raise
    except Exception as exc:  # a failed synthesis must not lose the advisors' artifacts
        log.exception("synthesis failed")
        record.artifacts.append(ArtifactRecord(SYNTHESIS_ROLE, None, None, error=repr(exc)))
        append_log({"event": "synthesis_error", "run_id": run_id, "error": repr(exc)}, log_file)
        return
    s_crit = None
    s_revised = False
    if critique:
        try:
            new_text, s_review, s_crit, c_flags = critique_and_revise(
                SYNTHESIS_ROLE, task, "", s_text, llm
            )
            s_revised = new_text != s_text
            s_text = new_text
            s_flags = s_flags + c_flags
        except Exception as exc:  # same rule as the specialists
            log.exception("critique of synthesis failed")
            append_log(
                {
                    "event": "critique_error",
                    "run_id": run_id,
                    "role": SYNTHESIS_ROLE,
                    "error": repr(exc),
                },
                log_file,
            )
    s_path = out / f"{SYNTHESIS_ROLE}.md"
    s_path.write_text(s_text, encoding="utf-8")
    regs = parse_registers(s_text)
    record.artifacts.append(
        ArtifactRecord(
            SYNTHESIS_ROLE,
            s_path.name,
            asdict(s_review) | {"verdict": s_review.verdict},
            sha256=sha256_text(s_text),
            critique=s_crit.as_dict() if s_crit else None,
            revised=s_revised,
            process_flags=s_flags,
        )
    )
    record.synthesis = {
        "role": SYNTHESIS_ROLE,
        "decisions": len(regs["decisions"]),
        "disagreements": len(regs["disagreements"]),
        "escalations": len(regs["escalations"]),
    }
    append_log({"event": "synthesis", "run_id": run_id, **record.synthesis}, log_file)


def run(
    task: str,
    *,
    llm: LLMClient | None = None,
    router: Router | None = None,
    root: Path | None = None,
    log_file: Path | None = None,
    critique: bool = True,
) -> RunRecord:
    """Route a task, run specialists in order, governance-check each artifact, park in pending/.

    The manifest is written before the first specialist runs and after every artifact, so an
    interrupted run is still visible (status 'running') and can be rejected by a human.
    """
    if not task or not task.strip():
        raise ValueError("task must be a non-empty string")
    if len(task) > MAX_TASK_CHARS:
        raise ValueError(f"task is {len(task)} chars; keep it under {MAX_TASK_CHARS}")
    # Governance only ever saw model output, but the task is written to the manifest and the
    # audit log, so PII in the input would bypass the check entirely.
    task_pii = [i for i in review_text(task).issues if i.startswith("Possible PII")]
    if task_pii:
        raise ValueError(f"task contains {'; '.join(task_pii)}; remove it before running")
    llm = llm or get_llm()
    router = router or Router()
    plan: Plan = router.route(task)
    run_id = new_run_id()
    record = RunRecord(
        run_id=run_id,
        task=task,
        provider=llm.name,
        plan={"roles": plan.roles, "matched_rules": plan.matched_rules},
        created_at=now_iso(),
    )
    out = run_dir(artifact_root(root), "pending", run_id)
    out.mkdir(parents=True, exist_ok=False)  # a collision is a bug, never a silent merge
    write_lock(out)  # tells the gate a live process owns this directory
    write_manifest(out, asdict(record))
    append_log(
        {
            "event": "run_start",
            "run_id": run_id,
            "task": task,
            "roles": plan.roles,
            "provider": llm.name,
        },
        log_file,
    )
    log.info("run %s: %d specialist(s) %s", run_id, len(plan.roles), plan.roles)

    context_parts: list[str] = []
    for role_key in plan.roles:
        try:
            text, review, flags = produce(role_key, task, llm, "\n\n".join(context_parts))
        except ProviderConfigError:
            # Every remaining specialist would fail identically, so stop and surface it once
            # rather than burying the provider's own explanation under N tracebacks.
            append_log({"event": "provider_config_error", "run_id": run_id}, log_file)
            write_manifest(out, asdict(record))
            clear_lock(out)
            raise
        except Exception as exc:  # one failing specialist must not hide the others
            log.exception("specialist %s failed", role_key)
            record.artifacts.append(ArtifactRecord(role_key, None, None, error=repr(exc)))
            append_log(
                {
                    "event": "specialist_error",
                    "run_id": run_id,
                    "role": role_key,
                    "error": repr(exc),
                },
                log_file,
            )
        else:
            crit = None
            revised = False
            if critique and role_key != CRITIC_ROLE:
                try:
                    new_text, review, crit, crit_flags = critique_and_revise(
                        role_key, task, "\n\n".join(context_parts), text, llm
                    )
                    revised = new_text != text
                    text = new_text
                    flags = flags + crit_flags
                except Exception as exc:  # a failed critique must not lose the draft
                    log.exception("critique of %s failed", role_key)
                    append_log(
                        {
                            "event": "critique_error",
                            "run_id": run_id,
                            "role": role_key,
                            "error": repr(exc),
                        },
                        log_file,
                    )
            if plan.used_default:
                flags = [*flags, DEFAULT_PLAN_FLAG]
            path = out / f"{role_key}.md"
            path.write_text(text, encoding="utf-8")
            review_dict = asdict(review) | {"verdict": review.verdict}
            record.artifacts.append(
                ArtifactRecord(
                    role_key,
                    path.name,
                    review_dict,
                    sha256=sha256_text(text),
                    critique=crit.as_dict() if crit else None,
                    revised=revised,
                    process_flags=flags,
                )
            )
            if crit:
                append_log(
                    {
                        "event": "critique",
                        "run_id": run_id,
                        "role": role_key,
                        "critic": crit.critic_role,
                        "points": len(crit.points),
                        "accepted": sum(1 for p in crit.points if p.disposition == "accepted"),
                        "unresolved_blocking": len(crit.blocking_unresolved),
                        "revised": revised,
                    },
                    log_file,
                )
            context_parts.append(f"[{get_role(role_key).title}]\n{_excerpt(text)}")
            append_log(
                {
                    "event": "artifact",
                    "run_id": run_id,
                    "role": role_key,
                    "verdict": review.verdict,
                    "issues": review.issues,
                },
                log_file,
            )
        write_manifest(out, asdict(record))

    # ---- Engagement Lead: the one deliverable the client acts on -------------------------
    # Runs after every specialist, reads their artifacts in full, and integrates. A failure
    # here must never cost the specialist work that already succeeded.
    _do_synthesis(record, task, llm, out, run_id, log_file, critique)
    write_manifest(out, asdict(record))

    record.status = "pending"
    write_manifest(out, asdict(record))
    clear_lock(out)
    append_log(
        {
            "event": "run_end",
            "run_id": run_id,
            "governance_clean": record.all_approved_by_governance,
            "errors": sum(1 for a in record.artifacts if a.error),
        },
        log_file,
    )
    return record


def resynthesize(
    run_id: str,
    *,
    llm: LLMClient | None = None,
    root: Path | None = None,
    log_file: Path | None = None,
    critique: bool = True,
) -> RunRecord:
    """Retry the Engagement Lead against a pending run's specialist artifacts already on disk.

    A failed synthesis (an empty completion, a provider outage, a token cap that needed
    raising) must not force paying for every specialist again: this reads the artifacts a
    prior `run()` already wrote and re-runs only the one call that failed. Refuses to touch a
    run that isn't pending, is still owned by a live process, or already has a successful
    engagement_lead artifact — resynthesizing is a retry, not a way to overwrite a finished
    synthesis.
    """
    validate_run_id(run_id)
    root_path = artifact_root(root)
    found = find_run(root_path, run_id)
    if not found:
        raise StorageError(f"run '{run_id}' not found under {root_path}")
    state, out = found
    if state != "pending":
        raise StorageError(f"run '{run_id}' is {state}, not pending; nothing to resynthesize")
    if lock_holder_alive(out):
        raise StorageError(f"run '{run_id}' is still running (live orchestrator); wait for it")
    manifest = read_manifest(out)
    artifacts = [ArtifactRecord(**a) for a in manifest.get("artifacts", [])]
    if any(a.role == SYNTHESIS_ROLE and a.error is None for a in artifacts):
        raise StorageError(
            f"run '{run_id}' already has a successful engagement_lead artifact; "
            "reject it and start a new run instead of overwriting a finished synthesis"
        )
    # Drop any failed placeholder(s) from a prior attempt; _do_synthesis appends a fresh one.
    artifacts = [a for a in artifacts if a.role != SYNTHESIS_ROLE]
    if not any(not a.error for a in artifacts):
        raise StorageError(f"run '{run_id}' has no successful specialist artifact to synthesize")

    llm = llm or get_llm()
    record = RunRecord(
        run_id=manifest["run_id"],
        task=manifest["task"],
        provider=manifest.get("provider", llm.name),
        plan=manifest.get("plan", {}),
        artifacts=artifacts,
        status=manifest.get("status", "pending"),
        created_at=manifest.get("created_at", ""),
        version=manifest.get("version", __version__),
    )
    write_lock(out)
    try:
        _do_synthesis(record, record.task, llm, out, run_id, log_file, critique)
    finally:
        write_manifest(out, asdict(record))
        clear_lock(out)
    append_log({"event": "resynthesis", "run_id": run_id, "synthesis": record.synthesis}, log_file)
    return record
