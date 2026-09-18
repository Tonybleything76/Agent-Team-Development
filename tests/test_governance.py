import pytest

from huminloop import governance
from huminloop.governance import review_text

GOOD = (
    "Objective: Improve onboarding\nBody: details here\n"
    "Citations: https://example.com/source\nRisks: scope creep\nNext Steps: pilot in Q3\n"
)


def test_good_artifact_is_approved():
    r = review_text(GOOD)
    assert r.ok and r.verdict == "APPROVE" and r.issues == []


def test_missing_section_is_flagged():
    r = review_text(GOOD.replace("Risks: scope creep\n", ""))
    assert not r.ok and "Missing section: risks" in r.issues


def test_placeholder_section_is_flagged():
    # The v0.1 stubs shipped "Risks: ..." and passed; that must fail now.
    r = review_text(GOOD.replace("Risks: scope creep", "Risks: ..."))
    assert "Placeholder content in section: risks" in r.issues


def test_missing_citation_url_is_flagged():
    r = review_text(GOOD.replace("https://example.com/source", "internal memo"))
    assert "Missing https citation URL in Citations section" in r.issues


def test_pii_is_flagged():
    r = review_text(GOOD + "Contact: jane@example.com or 555-123-4567\n")
    assert "Possible PII: email address present" in r.issues
    assert "Possible PII: phone number present" in r.issues


def test_section_headings_are_case_insensitive():
    assert review_text(GOOD.upper().replace("HTTPS://", "https://")).ok


def test_empty_section_is_flagged_not_swallowed_by_next_heading():
    # Found by the eval (case g10): '\s*' after the colon ate the newline and read the next heading.
    r = review_text(GOOD.replace("Risks: scope creep", "Risks:"))
    assert "Placeholder content in section: risks" in r.issues


def test_markdown_style_headings_are_recognised():
    md = (
        "## Objective\nImprove onboarding\n**Body:** details here\n- Citations: https://x.io\n"
        "**Risks**\nscope creep\n### Next Steps:\npilot in Q3\n"
    )
    r = review_text(md)
    assert r.ok, r.issues


def test_url_on_the_line_after_citations_heading_is_accepted():
    r = review_text(
        GOOD.replace(
            "Citations: https://example.com/source", "Citations:\nhttps://example.com/source"
        )
    )
    assert r.ok, r.issues


def test_decorated_placeholders_are_flagged():
    for junk in ("TBD.", "TBD - fill in", "to be determined", "-", "..."):
        r = review_text(GOOD.replace("Risks: scope creep", f"Risks: {junk}"))
        assert "Placeholder content in section: risks" in r.issues, junk


def test_body_is_required_and_one_char_sections_are_too_short():
    r = review_text(GOOD.replace("Body: details here\n", ""))
    assert "Missing section: body" in r.issues
    r = review_text(GOOD.replace("Risks: scope creep", "Risks: r"))
    assert "Section too short: risks" in r.issues


def test_url_outside_citations_does_not_satisfy_citation_rule():
    r = review_text(
        GOOD.replace("Citations: https://example.com/source", "Citations: see memo")
        + "Ref https://x.io\n"
    )
    assert "Missing https citation URL in Citations section" in r.issues


def test_more_pii_shapes_are_flagged():
    r = review_text(
        GOOD
        + "Body2: call (555) 123-4567 or 5551234567, SSN 123-45-6789, card 4111 1111 1111 1111\n"
    )
    assert "Possible PII: phone number present" in r.issues
    assert "Possible PII: SSN-shaped number present" in r.issues
    assert "Possible PII: card-shaped number present" in r.issues


def test_bare_section_word_in_prose_is_not_a_heading():
    r = review_text(GOOD.replace("Body: details here", "Body: Risks are discussed below in detail"))
    assert r.ok, r.issues


def test_numbered_markdown_headings_are_recognised():
    md = (
        "## 1. Objective\nImprove X\n## 2. Body\nDetails here\n## 3. Citations\nhttps://a.b\n"
        "## 4. Risks\nsome risk\n## 5. Next Steps\ngo live\n"
    )
    r = review_text(md)
    assert r.ok, r.issues


def test_body_bullet_starting_with_a_section_word_is_not_a_heading():
    text = (
        "Objective: Improve X\nBody: intro\n- Next steps schedule workshop\n- Risks of delay\n"
        "Citations: https://a.b\nRisks: some\nNext Steps: TBD\n"
    )
    r = review_text(text)
    assert "Placeholder content in section: next steps" in r.issues
    text2 = GOOD.replace(
        "Body: details here", "Body:\n- Objective 1 reduce cost\n- Objective 2 grow"
    )
    assert review_text(text2).ok, review_text(text2).issues


def test_plain_figures_and_year_lists_are_not_pii():
    r = review_text(
        GOOD.replace("Body: details here", "Body: population 1400000000 across 2026 2027 2028 2029")
    )
    assert r.ok, r.issues
    assert review_text(GOOD + "Card 4111 1111 1111 1111\n").issues == [
        "Possible PII: card-shaped number present"
    ]


def test_pluralised_labels_are_accepted():
    r = review_text(GOOD.replace("Objective:", "Objectives:").replace("Next Steps:", "Next Step:"))
    assert r.ok, r.issues


def test_bold_section_word_in_prose_is_not_a_heading():
    text = (
        "Objective: Improve onboarding\nBody: intro.\n**Risks** of delay are real, manageable.\n"
        "Citations: https://x.io/a\nRisks: TBD\nNext Steps: pilot in Q3\n"
    )
    assert "Placeholder content in section: risks" in review_text(text).issues


# ---------------------------------------------------------------------------
# one_line: safe to print on one row, and unable to lie about being safe.
# ---------------------------------------------------------------------------

_ROW_BREAKERS = [
    "\x00",
    "\t",
    "\n",
    "\x0b",
    "\x0c",
    "\x1b",
    "\x85",
    "​",
    " ",
    " ",
    "‮",
    "⁦",
    "﻿",
]


@pytest.mark.parametrize("ch", _ROW_BREAKERS, ids=[hex(ord(c)) for c in _ROW_BREAKERS])
def test_one_line_neutralises_everything_that_can_break_a_row(ch):
    """The first version used the C1 class only, so U+2028 -- legal in a POSIX filename --
    forged a whole extra row with no sign anything had happened."""
    out = governance.one_line(f"a{ch}b.md")
    assert not governance._LINE_UNSAFE_RE.search(out)  # nothing survives to break the row
    assert out != f"a{ch}b.md"  # and the reader can see it was not a plain name


def test_a_filename_cannot_forge_the_cleaned_notice():
    """The old form appended "[control characters removed]", which a filename can contain --
    the same plant-the-system's-own-notice hole fenced() closes for markers."""
    faked = governance.one_line("notes.md  [control characters removed]")
    real = governance.one_line("notes.md\x01")
    assert faked != real
    assert faked == "notes.md  [control characters removed]"  # shown as the plain text it is
    assert real.startswith("'") and "\\x01" in real  # genuinely odd names are quoted


def test_one_line_caps_only_when_a_limit_is_asked_for():
    """A filename shares a row with other columns and is bounded. A directory path stands on
    its own line and must never be cut, or the prompt stops saying where the material is."""
    assert governance.one_line("z" * 500) == "z" * 500  # unbounded by default
    capped = governance.one_line("z" * 500, governance.LINE_MAX_CHARS)
    assert len(capped) == governance.LINE_MAX_CHARS
    assert capped.endswith("...")  # stated, not silently truncated


def test_one_line_leaves_an_ordinary_name_exactly_alone():
    assert governance.one_line("2026-09-10-discovery-notes.md") == "2026-09-10-discovery-notes.md"
