Objective: Decide whether to scale the claims copilot across all three functions now, or gate one bounded phase first — and if the latter, which function, who owns it, and what closes before go-live.

Body:

## Recommendation
Do not approve a three-function scale-up in one motion. The committee is being asked to approve what is really three deployments plus an unbuilt architecture, with no named process owner in any function and no end-to-end human-in-the-loop map for any of them. Recommend closing five cross-cutting blockers — a named owner per process, EU AI Act classification from Legal, an end-to-end oversight map, claims data remediation, and a model/integration decision — then running one function as a bounded, evidence-gated proof phase, not two or three simultaneously. The sentence that survives if the rest is lost: nothing scales until someone is named who can be held accountable when the copilot is wrong, and no such person exists today for any of the three functions.

## Decisions
1. Which function opens first, and are the other two explicitly paused (not just deprioritized) until it clears proof criteria? -> Steering committee sponsor
2. Can three distinct, empowered owners — authority to change workflow, budget tied to the benefit, accountability for harm — be named, or does an unowned workstream pause rather than get a placeholder owner? -> Steering committee
3. Which named role holds override authority at the human-in-the-loop checkpoint, with confirmed time allocation and cover to reverse the model? -> Sponsor and line managers, jointly
4. Do we build audit and oversight controls now as if high-risk classification applies, or wait for Legal's ruling? -> Legal counsel
5. Does scaling into member services or claims imply headcount reduction, and will that be stated explicitly to the committee rather than folded into "efficiency"? -> Sponsor
6. What is the numeric accuracy target and population per function, without which data sign-off and model selection cannot proceed? -> Claims business lead

## Disagreements
1. Workstream input favoring member services first (lower stakes, cleaner proof of the oversight pattern) conflicts with input anchoring on claims as the pilot's natural home. We lean toward member services: claims data remediation appears to need 5–10 business days plus governance rulings, while the member services gap is a missing task spec, fixable in 1–2 weeks — a faster, cleaner first gate. This is a judgment call on timelines, not a settled fact.
2. One line of input reads as a full hold on all three functions until classification lands; another supports letting one function proceed under strict proof criteria while the rest wait. We lean toward staged rollout, but the underlying legal characterization of member services' risk tier is unverified and must come from Legal before this is more than a working assumption.

## Escalations
1. Is there a commercial or external commitment fixing a go-live date? That would explain pressure to scale all three functions at once despite two unnamed behind-schedule workstreams — only the sponsor can answer this.
2. Does leadership want to state now, explicitly, whether headcount reduction is part of this scale-up, or is that genuinely undecided?
3. Sequencing turns on confirmed completion dates for claims data remediation and the member services task spec — get both in writing before locking which function opens first.

Citations:
- EU AI Act, Annex III high-risk use cases: https://artificialintelligenceact.eu/annex/3/
- EU AI Act, Article 14 human oversight: https://artificialintelligenceact.eu/article/14/
- GDPR Art. 9, special category data: https://gdpr-info.eu/art-9-gdpr/

Risks: No Legal or DPO classification memo exists yet; this is a live, unowned gap, not a formality, and proceeding before it lands risks retroactive conformity failure rather than a paperwork delay. Two workstreams are behind schedule with no name attached to either, so impact is unassessable. Any informal override of a pause by the sponsor must be recorded in writing naming the risk accepted, or oversight is decorative. Claims data quality feeding a scaled model risks reproducing historical denial patterns against whatever subgroup was already denied more, and this is currently unmeasured.

Next Steps:
1. Sponsor decides function sequencing and pause status for the other two within one week, and confirms whether a commercial deadline is driving the three-function ask.
2. Legal issues a written Annex III classification memo before any further design commitment.
3. Frontline readiness interviews run this week in claims and member services to test whether resistance stems from an unnamed ownership gap.
4. Data remediation and task-spec owners confirm completion dates in writing before go-live sequencing is locked.