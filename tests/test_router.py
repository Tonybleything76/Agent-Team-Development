import pytest

from huminloop.roles import SPECIALISTS
from huminloop.router import ROUTING_RULES, Router


@pytest.fixture
def router():
    return Router()


def test_whole_word_matching_prevents_substring_hits(router):
    # 'nda' must not fire inside 'agenda'; 'msa' must not fire inside 'msatellite'.
    plan = router.route("Schedule the weekly agenda for the kickoff meeting")
    assert "legal" not in plan.matched_rules
    # Nothing else claims scheduling either, now that the agency roles are gone.
    assert plan.used_default


def test_plural_keyword_matches(router):
    assert router.route("Sign the NDAs").roles == ["legal"]


def test_multiple_rules_merge_in_order_without_duplicates(router):
    # 'strategy' and 'analytics' both dispatch data_scientist; it must appear once, in the
    # position the first matching rule gave it, with privacy's roles appended after.
    plan = router.route(
        "Build the transformation roadmap, define the KPIs, and write the data retention policy"
    )
    assert plan.matched_rules == ["strategy", "analytics", "privacy"]
    assert plan.roles == ["strategist", "data_scientist", "privacy", "legal"]
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


def test_transformation_advisors_are_all_reachable():
    """Every advisor added in v0.7.0 must have at least one rule that dispatches to it.

    The roster shipped before the routing did, so this is the guard against that recurring: a
    seat nobody can reach is worse than no seat, because the roster implies it works.
    """
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
    routed = {r for _, _, roles in ROUTING_RULES for r in roles}
    assert advisors <= routed, f"unreachable advisors: {sorted(advisors - routed)}"


def test_transformation_keywords_do_not_fire_on_the_pinned_strings(router):
    # The strings other tests pin. If a new keyword fires on any of them the dispatch order
    # changes silently, so assert the rule names directly rather than only the roles.
    assert router.route("Schedule the weekly agenda for the kickoff meeting").used_default
    assert router.route(
        "Build the transformation roadmap, define the KPIs, and write the data retention policy"
    ).matched_rules == ["strategy", "analytics", "privacy"]
    assert router.route("Of course we should start with a roadmap").matched_rules == ["strategy"]


def test_advisor_leads_when_a_transformation_rule_matches_alone(router):
    plan = router.route("How do we handle the resistance before go-live?")
    assert plan.matched_rules == ["change_adoption"]
    assert plan.roles == ["change_management_lead"]


def test_transformation_block_dispatches_in_engagement_order(router):
    # Two advisors on one task combine in ROUTING_RULES order, not in mention order: the seat
    # that owns the outcome is briefed before the seat that redesigns the work.
    plan = router.route("Where does the handoff sit once we own the claims process end to end?")
    assert plan.roles == ["domain_owner", "process_excellence_lead"]


def test_staffing_explains_who_was_dispatched_and_who_was_not(router):
    task = "Design an AI enablement and adoption program for field technicians"
    plan = router.route(task)
    s = router.staffing(task, plan)

    dispatched = {d["role"]: d["why"] for d in s["dispatched"]}
    assert set(dispatched) == set(plan.roles)
    # Each dispatched advisor names the rule and the word that summoned it.
    assert "adoption" in dispatched["change_management_lead"]
    assert "change_adoption" in dispatched["change_management_lead"]

    absent = {a["role"]: a["would_join_on"] for a in s["absent"]}
    assert not set(absent) & set(plan.roles)
    assert "legal" in absent and "nda" in absent["legal"]


def test_staffing_names_the_default_when_no_rule_fired(router):
    task = "xyzzy plugh"
    plan = router.route(task)
    s = router.staffing(task, plan)
    assert plan.used_default
    assert "no rule matched" in s["dispatched"][0]["why"]


def test_every_specialist_is_reachable_by_some_rule(router):
    """An advisor no rule can reach is a router gap, not a staffing judgement."""
    plan = router.route("xyzzy plugh")
    assert router.staffing("xyzzy plugh", plan)["unreachable"] == []
