from adeptly.governance import review_text

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
