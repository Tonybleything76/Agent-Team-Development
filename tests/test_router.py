import pytest

from adeptly.roles import SPECIALISTS
from adeptly.router import ROUTING_RULES, Router


@pytest.fixture
def router():
    return Router()


def test_whole_word_matching_prevents_substring_hits(router):
    # 'nda' must not fire inside 'agenda'; 'msa' must not fire inside 'msatellite'.
    plan = router.route("Schedule the weekly agenda and travel for the kickoff meeting")
    assert plan.roles == ["legal"]  # CI PROOF: deliberately wrong; reverted in the next commit
    assert "legal" not in plan.matched_rules


def test_plural_keyword_matches(router):
    assert router.route("Sign the NDAs").roles == ["legal"]


def test_multiple_rules_merge_in_order_without_duplicates(router):
    plan = router.route("Write a blog and a LinkedIn thread about the campaign")
    assert plan.matched_rules == ["campaign", "social"]
    assert plan.roles == ["marketing", "content_creator", "social_manager"]
    assert len(plan.roles) == len(set(plan.roles))


def test_default_fallback_when_nothing_matches(router):
    plan = router.route("xyzzy plugh")
    assert plan.roles == ["strategist"]
    assert plan.used_default


def test_every_rule_targets_known_specialists():
    for name, _, roles in ROUTING_RULES:
        for r in roles:
            assert r in SPECIALISTS, f"rule {name} names unknown role {r}"


def test_router_rejects_rules_naming_unknown_roles():
    with pytest.raises(ValueError):
        Router(rules=[("bad", ("x",), ("not_a_role",))])


def test_supervisors_are_never_routed_to(router):
    for _, keywords, _ in ROUTING_RULES:
        plan = router.route(" ".join(keywords))
        assert "router" not in plan.roles and "governance" not in plan.roles


def test_router_rejects_unknown_default_roles():
    with pytest.raises(ValueError, match="default"):
        Router(default=("nobody",))


def test_conversational_course_does_not_route_to_ld(router):
    assert router.route("Of course we should start with a roadmap").roles == [
        "strategist",
        "data_scientist",
    ]
