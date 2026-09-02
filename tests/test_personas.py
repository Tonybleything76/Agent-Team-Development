from huminloop.llm import build_prompt
from huminloop.personas import PERSONA_DIR, load_persona, persona_keys
from huminloop.roles import ROLES, SPECIALISTS, get_role

# Mirrors evals.run.PERSONA_SECTIONS. A persona that cannot say no will agree with whoever
# asked, so the refusal section is structural, not decorative.
REQUIRED_SECTIONS = ("## Remit", "## Output contract", "## Refuse or escalate")


def _persona_files():
    """Files that are meant to be role personas.

    Underscore-prefixed files are shared briefs. A dot in the stem marks a sibling written by
    local tooling (`domain_owner.plain.md`), which is gitignored and not a persona.
    """
    return [p for p in PERSONA_DIR.glob("*.md") if not p.stem.startswith("_") and "." not in p.stem]


def test_every_persona_file_names_a_real_role():
    """Catches the typo persona_keys() would otherwise skip in silence.

    `data_readiness.md` instead of `data_readiness_lead.md` would load for nobody, and the only
    symptom would be a specialist quietly producing generic output.
    """
    unknown = sorted(p.name for p in _persona_files() if p.stem not in ROLES)
    assert not unknown, f"persona files naming no known role: {unknown}"


def test_persona_keys_ignores_tooling_siblings(tmp_path, monkeypatch):
    """A gitignored `*.plain.md` twin must not become a phantom role and crash the eval."""
    import huminloop.personas as personas

    (tmp_path / "strategist.md").write_text("# S")
    (tmp_path / "strategist.plain.md").write_text("# S, simplified")
    (tmp_path / "_house.md").write_text("# house")
    (tmp_path / "not_a_role.md").write_text("# nope")
    monkeypatch.setattr(personas, "PERSONA_DIR", tmp_path)
    assert personas.persona_keys() == ["strategist"]


def test_every_persona_carries_the_required_sections():
    missing = {
        key: [s for s in REQUIRED_SECTIONS if s not in (load_persona(key) or "")]
        for key in persona_keys()
    }
    assert not {k: v for k, v in missing.items() if v}


def test_every_persona_reaches_its_specialist_prompt():
    for key in persona_keys():
        text = load_persona(key)
        system, _ = build_prompt(get_role(key), "eval task", "")
        assert text and text in system, f"{key} persona does not reach the prompt"


def test_the_eight_transformation_advisors_are_personified():
    """Milestone 1b's definition of done: no advisor left on a one-line remit."""
    advisors = {
        "domain_owner",
        "value_realization_lead",
        "change_management_lead",
        "process_excellence_lead",
        "data_readiness_lead",
        "enterprise_architect",
        "program_management_lead",
        "governance_advisor",
    }
    written = set(persona_keys())
    assert advisors <= written, f"unpersonified: {sorted(advisors - written)}"


def test_personas_only_exist_for_real_roles():
    """A persona for a key no role owns is a typo that would silently never be used.

    Supervisors are allowed one: the Engagement Lead is dispatched through synthesize()
    rather than produce(), and it needs more persona than any specialist.
    """
    assert set(persona_keys()) <= set(ROLES)


def test_supervisor_personas_do_not_inflate_specialist_coverage():
    """persona_coverage answers 'how many specialists have a point of view', so the
    Engagement Lead's persona must not be counted in that numerator."""
    specialist_personas = set(persona_keys()) & set(SPECIALISTS)
    assert "engagement_lead" in set(persona_keys())
    assert "engagement_lead" not in specialist_personas
