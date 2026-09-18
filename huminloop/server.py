"""A local review inbox for the gate.

The gate is an inbox: a queue of runs waiting on a person, each with artifacts to read, a
critique exchange to follow, and escalations to answer. A terminal is a poor inbox, so this
serves the same thing in a browser.

It adds no rules. Every decision goes through `gate.approve/reject/annotate/reopen`, so the
digest verification, the named approver, the forced-override record and the append-only history
are the ones already tested — there is no second implementation to drift.

Deliberately local and single-user: bound to the loopback interface, Host header checked to
defeat DNS rebinding, and a per-process token on every state-changing form so another site open
in the same browser cannot post decisions on your behalf. The gate records *that* a named human
decided; it still does not authenticate *who*, and a localhost server does not change that.
"""

import logging
import secrets
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import gate
from .render import RenderError, esc, render_run
from .storage import StorageError, artifact_root, find_run, read_manifest

log = logging.getLogger(__name__)
ALLOWED_HOSTS = {"localhost", "127.0.0.1", "[::1]"}
ESCALATION_PREFIX = "Escalated to the human:"
MAX_BODY = 64 * 1024


class ReviewState:
    """Process-wide server state: where runs live, and the token that guards POSTs."""

    def __init__(self, root: Path | None = None):
        self.root = artifact_root(root)
        self.token = secrets.token_urlsafe(24)


def _flags(artifact: dict) -> list[str]:
    # The manifest is editable. One non-string flag crashed the inbox list for every run, so
    # each is stringified; an odd value still shows up rather than disappearing.
    flags = artifact.get("process_flags") or []
    return [str(f) for f in flags] if isinstance(flags, list) else [str(flags)]


def escalations(manifest: dict) -> list[str]:
    out = []
    for artifact in manifest.get("artifacts", []):
        for flag in _flags(artifact):
            if flag.startswith(ESCALATION_PREFIX):
                out.append(flag[len(ESCALATION_PREFIX) :].strip())
    return out


def other_flags(manifest: dict) -> list[str]:
    out = []
    for artifact in manifest.get("artifacts", []):
        for flag in _flags(artifact):
            if not flag.startswith(ESCALATION_PREFIX):
                out.append(f"{artifact['role']}: {flag}")
    return out


def _row(manifest: dict, state: str) -> str:
    run_id = manifest.get("run_id", "?")
    task = esc(str(manifest.get("task") or "")[:120])
    # One edited manifest must not take down the list for every run: count only what has the
    # shape the gate writes.
    annotations = manifest.get("annotations")
    history = manifest.get("decisions")
    notes = len(annotations) if isinstance(annotations, list) else 0
    reopens = sum(
        1
        for d in (history if isinstance(history, list) else [])
        if isinstance(d, dict) and d.get("state") == "reopened"
    )
    asks = len(escalations(manifest))
    chips = ""
    if asks:
        chips += f'<span class="chip ask">{asks} for you</span>'
    if notes:
        chips += f'<span class="chip">{notes} note{"s" if notes > 1 else ""}</span>'
    if reopens:
        chips += '<span class="chip">reopened</span>'
    return (
        f'<a class="row" href="/run/{esc(run_id)}">'
        f'<span class="rid">{esc(run_id)}</span>'
        f'<span class="task">{task}</span>'
        f'<span class="chips">{chips}</span></a>'
    )


def inbox_page(state: ReviewState) -> str:
    sections = []
    for bucket, heading, empty in (
        ("pending", "Waiting on you", "Nothing is waiting."),
        ("approved", "Approved", None),
        ("rejected", "Rejected", None),
    ):
        runs = gate.list_runs(bucket, state.root)
        if not runs and bucket != "pending":
            continue
        rows = "".join(_row(m, bucket) for m in runs) or f'<p class="empty">{empty}</p>'
        sections.append(f"<h2>{heading}</h2><div class='rows'>{rows}</div>")
    return _shell("Review inbox", f"<h1>Review inbox</h1>{''.join(sections)}")


def _shell(title: str, body: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>
<style>
:root{{--ink:#1a1a2e;--body:#3d3d5c;--accent:#7a78f5;--surface:#fbfbfd;--line:#e6e6f0;
--warn:#b4453d;font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--surface);color:var(--body);line-height:1.6}}
main{{max-width:60rem;margin:0 auto;padding:2.5rem 1.25rem 4rem}}
h1{{font-family:"DM Sans",Inter,sans-serif;color:var(--ink);font-size:1.7rem;margin:0 0 1.5rem}}
h2{{font-family:"DM Sans",Inter,sans-serif;color:var(--ink);font-size:1rem;margin:2rem 0 .6rem;
text-transform:uppercase;letter-spacing:.06em;font-size:.78rem;color:#6b6b8a}}
.rows{{border:1px solid var(--line);border-radius:8px;overflow:hidden;background:#fff}}
.row{{display:flex;gap:1rem;align-items:center;padding:.8rem 1rem;
border-bottom:1px solid var(--line);
text-decoration:none;color:inherit}}
.row:last-child{{border-bottom:none}}.row:hover{{background:#f5f5fb}}
.rid{{font-family:ui-monospace,Menlo,monospace;font-size:.78rem;color:#6b6b8a;flex:0 0 auto}}
.task{{flex:1 1 auto;color:var(--ink)}}
.chips{{flex:0 0 auto;display:flex;gap:.35rem}}
.chip{{font-size:.7rem;padding:.15rem .5rem;border-radius:99px;background:#eeeef6;color:#5a5a80}}
.chip.ask{{background:#fdeceb;color:var(--warn);font-weight:600}}
.empty{{padding:1rem;color:#6b6b8a}}
.panel{{border:1px solid var(--line);border-radius:10px;background:#fff;padding:1.25rem;
margin:2rem 0}}
.panel h3{{font-family:"DM Sans",Inter,sans-serif;color:var(--ink);margin:0 0 .5rem;font-size:1rem}}
.asks{{border-left:3px solid var(--warn);padding-left:.9rem;margin:0 0 1rem}}
.asks li{{margin:.4rem 0}}
form{{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;margin:.6rem 0}}
input[type=text]{{flex:1 1 16rem;padding:.5rem .6rem;border:1px solid var(--line);border-radius:6px;
font:inherit;font-size:.9rem}}
button{{padding:.5rem .9rem;border:1px solid var(--accent);background:var(--accent);color:#fff;
border-radius:6px;font:inherit;font-size:.88rem;cursor:pointer}}
button.ghost{{background:#fff;color:var(--accent)}}
button.warn{{background:#fff;color:var(--warn);border-color:var(--warn)}}
.err{{background:#fdeceb;border:1px solid #f3c9c6;color:var(--warn);padding:.7rem .9rem;
border-radius:6px;margin:1rem 0}}
a.back{{font-size:.85rem}}
@media(prefers-color-scheme:dark){{:root{{--surface:#101021;--body:#c3c3d8;--ink:#f0f0f8;--line:#2a2a44}}
.rows,.panel{{background:#17172e}}.row:hover{{background:#1d1d38}}.chip{{background:#23233f;color:#a8a8c8}}}}
</style></head><body><main>{body}</main></body></html>"""


def _actions_html(state: ReviewState, run_id: str, bucket: str, manifest: dict) -> str:
    t = f'<input type="hidden" name="token" value="{esc(state.token)}">'
    who = '<input type="text" name="by" placeholder="Your name" required>'
    asks = escalations(manifest)
    flags = other_flags(manifest)
    parts = ['<div class="panel" id="decide"><h3>Your decision</h3>']
    if asks:
        parts.append(
            "<p>The team escalated "
            f"{len(asks)} question{'s' if len(asks) > 1 else ''} it says only you can answer. "
            "Until they are answered this run cannot be approved without an override.</p>"
            "<ul class='asks'>" + "".join(f"<li>{esc(a)}</li>" for a in asks) + "</ul>"
        )
    if flags:
        parts.append("<ul class='asks'>" + "".join(f"<li>{esc(f)}</li>" for f in flags) + "</ul>")
    if bucket == "pending":
        parts.append(
            f'<form method="post" action="/run/{esc(run_id)}/annotate">{t}{who}'
            '<input type="text" name="note" placeholder="A reservation, without deciding" required>'
            '<button class="ghost" type="submit">Add note</button></form>'
            f'<form method="post" action="/run/{esc(run_id)}/approve">{t}{who}'
            '<input type="text" name="note" placeholder="Note (required to override)">'
            '<label style="font-size:.85rem"><input type="checkbox" name="force" value="1"> '
            "override the flags</label>"
            '<button type="submit">Approve</button></form>'
            f'<form method="post" action="/run/{esc(run_id)}/reject">{t}{who}'
            '<input type="text" name="reason" placeholder="Why" required>'
            '<button class="warn" type="submit">Reject</button></form>'
        )
    else:
        parts.append(
            f"<p>This run is <b>{esc(bucket)}</b>. Reopening supersedes that decision without "
            "erasing it.</p>"
            f'<form method="post" action="/run/{esc(run_id)}/reopen">{t}{who}'
            '<input type="text" name="reason" placeholder="Why you are reopening" required>'
            '<button class="ghost" type="submit">Reopen</button></form>'
            f'<form method="post" action="/run/{esc(run_id)}/annotate">{t}{who}'
            '<input type="text" name="note" placeholder="Add a note" required>'
            '<button class="ghost" type="submit">Add note</button></form>'
        )
    parts.append("</div>")
    return "".join(parts)


_NO_WEB_FORM = {
    "wait": "The run is still being written. Reload this page when it finishes.",
    "resynthesize": "The lead's synthesis is missing. Run `huminloop resynthesize {run_id}` "
    "from the terminal, then reload this page.",
    # The gate would accept approve, but this page shows none of the content, and approving
    # what you cannot see here is exactly what the renderer's refusal exists to prevent.
    "approve": "The gate would accept an approval, but this page cannot show what you would "
    "be approving. Read it with `huminloop show {run_id}`, then run "
    "`huminloop approve {run_id} --by <your name>` from the terminal.",
}


def _recorded_decision(state: ReviewState, run_id: str) -> dict:
    """The recorded but unfinished decision, if any. Best effort: the page is a fallback."""
    found = find_run(state.root, run_id)
    if not found:
        return {}
    try:
        return gate.recorded_decision(read_manifest(found[1])) or {}
    except StorageError:
        return {}


def _unrenderable_page(
    state: ReviewState, run_id: str, reason: str, error: str | None
) -> tuple[int, str]:
    """A run the renderer refuses still needs a way out of the queue.

    Rendering attests to the bytes on disk, so this page shows none of them: only why the run
    cannot be shown, and the one move `gate.status` says the gate will accept. Offering any
    other would repeat the contradiction `pending_action` exists to prevent.
    """
    try:
        s = gate.status(run_id, root=state.root)
    except gate.GateError as exc:
        return 404, _shell("Not found", f'<p class="err">{esc(str(exc))}</p>')
    action = s["pending_action"]
    t = f'<input type="hidden" name="token" value="{esc(state.token)}">'
    who = '<input type="text" name="by" placeholder="Your name" required>'
    parts = [
        '<p><a class="back" href="/">&larr; Review inbox</a></p>',
        f"<h1>Run {esc(run_id)}</h1>",
        f'<div class="err">{esc(error)}</div>' if error else "",
        f"<p>This run cannot be shown: {esc(reason)}</p>",
        '<div class="panel" id="decide"><h3>Your decision</h3>',
    ]
    if action == "reject":
        recorded = _recorded_decision(state, run_id)
        if recorded.get("state") == "rejected":
            # Completing a recorded reject keeps that decision; the gate does not take a new one.
            why = (
                f"A reject by {esc(recorded.get('by'))} is already recorded but the move did not "
                "finish. Submitting completes that decision; its original reason is the one kept."
            )
        elif not s["artifacts_verified"] and not s["interrupted"]:
            why = (
                "Its contents cannot be verified, so it cannot be approved. Reject it and run the "
                "task again; the reason it failed verification is recorded with your decision."
            )
        else:
            why = "It did not finish, so it cannot be approved. Reject it and run the task again."
        parts.append(
            f"<p>{why}</p>"
            f'<form method="post" action="/run/{esc(run_id)}/reject">{t}{who}'
            '<input type="text" name="reason" placeholder="Why" required>'
            '<button class="warn" type="submit">Reject</button></form>'
        )
    elif action == "done":
        parts.append(
            f"<p>This run is <b>{esc(s['status'])}</b>. Reopening supersedes that decision "
            "without erasing it.</p>"
            f'<form method="post" action="/run/{esc(run_id)}/reopen">{t}{who}'
            '<input type="text" name="reason" placeholder="Why you are reopening" required>'
            '<button class="ghost" type="submit">Reopen</button></form>'
        )
    else:
        parts.append(f"<p>{esc(_NO_WEB_FORM.get(action, action).format(run_id=run_id))}</p>")
    parts.append("</div>")
    return 200, _shell(f"Run {run_id}", "".join(parts))


def run_page(state: ReviewState, run_id: str, error: str | None = None) -> tuple[int, str]:
    try:
        found = find_run(state.root, run_id)
    except StorageError as exc:
        return 400, _shell("Not found", f'<p class="err">{esc(str(exc))}</p>')
    if not found:
        # `find_run` needs a manifest; a run that died before writing one still sits in the
        # inbox, and `gate.status` knows what to do with it.
        return _unrenderable_page(state, run_id, "no manifest was written", error)
    bucket, d = found
    try:
        manifest = read_manifest(d)
        page = render_run(manifest, d)
    except (gate.GateError, RenderError, StorageError) as exc:
        return _unrenderable_page(state, run_id, str(exc), error)
    except Exception as exc:  # noqa: BLE001
        # A manifest edited into a shape the renderer never expected (a `plan` that is a
        # string) used to drop the connection, leaving the web no way to reject the run.
        # Logged, because the same fallback would otherwise hide a real renderer bug.
        log.exception("run %s could not be rendered; serving the fallback page", run_id)
        return _unrenderable_page(
            state, run_id, f"the page could not be built ({type(exc).__name__})", error
        )
    banner = f'<div class="err">{esc(error)}</div>' if error else ""
    nav = '<p><a class="back" href="/">&larr; Review inbox</a></p>'
    panel = _actions_html(state, run_id, bucket, manifest)
    # render_run owns the page; the panel is appended to it rather than rebuilt around it.
    injected = f"{nav}{banner}{panel}{_shell('', '')[:0]}"
    marker = "</main>"
    if marker in page:
        page = page.replace(marker, injected + marker, 1)
    else:
        page += injected
    return 200, page


class Handler(BaseHTTPRequestHandler):
    server_version = "huminloop"
    state: ReviewState

    def log_message(self, fmt, *args):  # quieter than the default stderr firehose
        pass

    def _send(self, code: int, body: str):
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(raw)

    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        return host in ALLOWED_HOSTS

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, _shell("Forbidden", "<p>Unrecognised Host header.</p>"))
        path = urlparse(self.path).path
        if path == "/":
            return self._send(200, inbox_page(self.state))
        if path.startswith("/run/"):
            run_id = path.split("/")[2]
            code, page = run_page(self.state, run_id)
            return self._send(code, page)
        self._send(404, _shell("Not found", "<p>No such page.</p>"))

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, _shell("Forbidden", "<p>Unrecognised Host header.</p>"))
        parts = urlparse(self.path).path.strip("/").split("/")
        if len(parts) != 3 or parts[0] != "run":
            return self._send(404, _shell("Not found", "<p>No such action.</p>"))
        _, run_id, action = parts
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY)
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        one = lambda k: (form.get(k) or [""])[0].strip()  # noqa: E731

        if not secrets.compare_digest(one("token"), self.state.token):
            # Another site open in this browser must not be able to decide on your behalf.
            code, page = run_page(
                self.state, run_id, "Stale or missing form token; reload and retry."
            )
            return self._send(code, page)

        by = one("by")
        try:
            if action == "approve":
                gate.approve(
                    run_id, by, one("note"), force=bool(one("force")), root=self.state.root
                )
            elif action == "reject":
                gate.reject(run_id, by, one("reason"), root=self.state.root)
            elif action == "annotate":
                gate.annotate(run_id, by, one("note"), root=self.state.root)
            elif action == "reopen":
                gate.reopen(run_id, by, one("reason"), root=self.state.root)
            else:
                return self._send(404, _shell("Not found", "<p>No such action.</p>"))
        except (gate.GateError, StorageError) as exc:
            code, page = run_page(self.state, run_id, str(exc))
            return self._send(code, page)
        self.send_response(303)
        self.send_header("Location", f"/run/{run_id}")
        self.end_headers()


def serve(
    host: str = "127.0.0.1", port: int = 8765, root: Path | None = None, open_browser: bool = True
):
    if host not in ("127.0.0.1", "localhost", "::1"):
        # There is no authentication here; binding wider would publish the gate to the network.
        raise ValueError(f"refusing to bind {host}: this server is loopback-only by design")
    handler = type("BoundHandler", (Handler,), {"state": ReviewState(root)})
    httpd = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{httpd.server_address[1]}/"
    print(f"review inbox at {url}   (ctrl-c to stop)")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        httpd.server_close()
    return httpd
