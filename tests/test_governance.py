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
    assert "Missing citation URL(s)" in r.issues


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
