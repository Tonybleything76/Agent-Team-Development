# Roster Evidence — how tier-one consultancies staff AI transformation engagements

> Source: Gemini Deep Research Agent, run 2026-08-26. 17 grounded searches, 47 cited sources.
> Commissioned to answer one question: what roles actually staff a Big Four AI transformation
> engagement, and what decision does each own. This document is the evidence base for the
> role registry in `huminloop/roles.py`.
>
> **On the links:** citations resolve to canonical publisher URLs (re-resolved 2026-09-02 from
> the original Vertex AI Search redirects, each verified live). A few — bcg.com, mckinsey.com,
> medium.com, researchgate.net — block automated fetching (403 or connection refused on a bare
> request); those were confirmed live by other means (full-browser fetch, or content matching
> the specific claim cited) rather than a plain HTTP check. Four accenture.com citations
> [17, 18, 21, 26] resolved to generic careers-search landing pages rather than the specific
> job posting originally grounded — the role and firm are still correctly attributed, but a
> reader following the link will land on a search index, not one exact requisition.

---

# Enterprise AI Transformation Engagements: An Analysis of Team Composition, Roles, and Governance in Tier-One Consultancies

**Key Points:**
*   **The 10-20-70 Paradigm Shift:** Research suggests that AI transformation is fundamentally shifting from a technology-centric to an organizational-centric model. The BCG 10-20-70 rule postulates that only 10% of value is derived from algorithms and 20% from technology, whereas 70% relies on people, processes, and change management [cite: 1, 2]. 
*   **Bifurcation of Leadership Roles:** The traditional "IT Project Manager" is being replaced by a dual-leadership model. The "Domain Owner" (a business executive) owns the strategic outcome and workflow redesign [cite: 3, 4], while the "AI Product Manager" or "Enterprise Architect" owns the technical delivery [cite: 4, 5].
*   **The POC Proliferation Problem:** Evidence strongly leans toward the conclusion that AI engagements fail most frequently due to an understaffed "Business Application Layer" and missing Change Management roles, leading to disconnected pilots that fail to scale or generate P&L impact [cite: 6, 7].

**Introduction to the Research Context**
Understanding how Big Four accounting firms (Deloitte, PwC, EY, KPMG) and premier strategy/technology consultancies (McKinsey, BCG, Accenture, IBM) staff Artificial Intelligence (AI) transformation engagements requires piercing through layers of capability marketing to isolate actionable delivery structures. The enterprise AI transformation landscape is highly complex, blending software engineering with sociotechnical organizational redesign [cite: 7, 8]. 

**Methodological Limitations and Hedging**
It seems likely that consultancies heavily guard their exact internal operating models and leverage pyramids. Thus, this report triangulates the "canonical" engagement team composition by analyzing public-facing job requisitions, published frameworks (e.g., IBM Garage, Deloitte Trustworthy AI), analyst observations, and practitioner literature. While rate cards are rarely publicized in full, extant data from government procurement and executive hiring patterns provide a defensible proxy for how these teams are structured [cite: 9, 10]. The following sections directly address the structural, functional, and governance mechanisms of enterprise AI transformation delivery teams.

---

## 1. Executive Summary: The Canonical Engagement Team

A typical enterprise AI transformation engagement team deployed by a top-tier consultancy operates as a cross-functional, multi-tiered unit designed to bridge the gap between algorithmic potential and realized business value. At the apex sits the **Engagement Partner / Executive Sponsor**, who manages the client C-suite relationship and owns the ultimate commercial and strategic outcomes [cite: 11, 12]. Reporting to them is a dual-leadership core: the **Domain Owner (or AI Transformation Lead)**, a tech-fluent business expert who owns the process redesign and use-case roadmaps [cite: 3, 4], and the **Enterprise Architect (or AI Tech Lead)**, who owns the technical ecosystem and model integration [cite: 4, 5]. Beneath this leadership layer, the delivery apparatus is divided into specialized agile squads (often mirroring the IBM Garage model of 7-10 "T-shaped" individuals) [cite: 5, 13]. These squads comprise **AI Product Managers** defining requirements, **Forward Deployed Engineers / Data Scientists** executing model development [cite: 14], and **Data Architects** ensuring data readiness [cite: 15]. Operating in parallel to technical delivery are the assurance and adoption functions: the **AI Governance / Trustworthy AI Manager** who signs off on risk, ethics, and compliance [cite: 16], and the **Change Management & Adoption Lead**, who owns workforce reskilling, UX/AX (Agentic Experience) design, and the ultimate operationalization of the technology [cite: 1, 17].

---

## 2. Engagement Workstreams

An enterprise AI transformation is not treated as a monolithic IT implementation; rather, it is divided into distinct workstreams that operate concurrently. Based on frameworks from McKinsey [cite: 3], Accenture [cite: 17, 18], and IBM [cite: 5, 19], the typical engagement comprises the following workstreams:

### A. Strategy, Portfolio, and Value Realization
*   **Lead Role:** AI Transformation Value Realization Lead / Engagement Manager [cite: 10, 20].
*   **Scope:** This workstream focuses on the overarching business case. It is responsible for identifying the initial use cases, prioritizing them in an AI portfolio, mapping out ROI targets, and ensuring that the transformation translates into measurable P&L impact (e.g., revenue growth, cost reduction, cycle time improvement) [cite: 10, 20].

### B. Business Process and Workflow Redesign (The "Domain")
*   **Lead Role:** Domain Owner (McKinsey terminology) or AI Process Excellence Manager (Accenture terminology) [cite: 3, 21].
*   **Scope:** Moving beyond isolated automation, this workstream reimagines the end-to-end business process. It identifies where human judgment is required versus where an AI agent can execute tasks autonomously. It focuses heavily on "AX Design" (Agentic Experience design)—the intersection of human, agent, and process [cite: 14, 17].

### C. Technical Delivery and Architecture
*   **Lead Role:** Enterprise Architect / AI Tech Lead [cite: 4, 5].
*   **Scope:** Operating typically on agile or DevSecOps methodologies (e.g., IBM Garage's "Co-execute" phase), this workstream handles the actual engineering [cite: 13, 19]. It includes building LLM wrappers, orchestrating multi-agent systems, integrating APIs with core enterprise systems, and managing site reliability engineering (SRE) [cite: 5].

### D. Data Readiness and Infrastructure
*   **Lead Role:** Data Architect / Chief Data Officer (Advisory) [cite: 15, 22].
*   **Scope:** This workstream ensures the underlying data is accessible, clean, and structured. It encompasses data curation, establishing data pipelines, and migrating server/cloud infrastructure necessary to support high-compute AI models [cite: 9, 22].

### E. AI Governance, Risk, and Compliance
*   **Lead Role:** AI Governance Manager (e.g., Deloitte Trustworthy AI Lead) [cite: 16].
*   **Scope:** This critical assurance workstream ensures the AI system adheres to regulatory standards (e.g., EU AI Act), privacy constraints, and ethical mandates. It operationalizes frameworks that test for fairness, transparency, robustness, and security [cite: 23, 24].

### F. Change Management, Adoption, and Workforce Readiness
*   **Lead Role:** AI Change Management Lead / AI Strategic Advisor [cite: 20, 25].
*   **Scope:** Addressing the "70%" of the BCG 10-20-70 rule, this workstream is responsible for mitigating employee resistance, restructuring job roles, conducting AI literacy upskilling, and driving user adoption metrics [cite: 1, 2].

---

## 3. Role Roster Table

The following table synthesizes the named functional roles on the delivery team, derived from specific job requisitions, rate cards, and published methodologies from the target consultancies. 

| Role Name | Tier (client-facing / delivery / assurance) | Decision It Owns | Evidence Strength (strong / moderate / thin) | Primary Citation |
| :--- | :--- | :--- | :--- | :--- |
| **Domain Owner / Business Lead** | Client-Facing | Decides which end-to-end business processes are redesigned; signs off on final workflow changes and business value realization. | Strong | [cite: 3, 4] |
| **AI Transformation / Engagement Manager** | Delivery | Owns sprint execution, resource allocation, cross-team coordination, and day-to-day project timeline delivery. | Strong | [cite: 16, 26] |
| **Value Realization Lead** | Client-Facing | Owns the business case baseline; decides the metrics for ROI/productivity; signs off on whether a pilot has met financial criteria to scale. | Strong | [cite: 10, 20] |
| **AI Process Excellence / AX Designer** | Delivery | Owns the future-state process map; decides the exact interaction points between human employees and AI agents (human-in-the-loop design). | Strong | [cite: 17, 21] |
| **Enterprise AI Architect** | Delivery | Decides the technological ecosystem (cloud, LLM selection, data pipelines); owns the overarching system integration blueprint. | Moderate | [cite: 4, 5] |
| **Forward Deployed Engineer / AI Developer** | Delivery | Owns the codebase; decides the implementation logic for the model and orchestration layers; signs off on technical testing/QA. | Strong | [cite: 5, 14] |
| **Data Architect / CDO Advisor** | Delivery | Owns data pipeline readiness; decides which internal/external datasets are approved for model training/fine-tuning. | Moderate | [cite: 15, 22] |
| **AI Governance / Risk Manager** | Assurance | Owns the ethical/compliance gate; has the authority to reject models that fail bias, privacy, or security testing (Trustworthy AI). | Strong | [cite: 16] |
| **Change Management & Adoption Lead** | Client-Facing | Owns the organizational readiness plan; decides the training curriculum; signs off on the communications and role-redesign strategies. | Strong | [cite: 1, 20] |
| **AI Product Manager** | Delivery | Decides the feature backlog and user stories; signs off on whether the MVP meets the minimum functional requirements for users. | Strong | [cite: 6, 27] |

---

## 4. Where Governance and Change Management Sit

### AI Governance and Responsible AI
In top-tier consultancies, AI Governance is not relegated to a downstream compliance check; it is established as a parallel, cross-functional oversight apparatus [cite: 28, 29]. In models like Deloitte's Trustworthy AI framework, governance experts are embedded across the AI lifecycle—from ideation to monitoring [cite: 23, 28]. 
*   **Placement & Reporting:** The AI Governance Manager typically reports directly to the Engagement Partner or sits within the client's AI Center of Excellence (CoE) steering committee [cite: 29, 30]. 
*   **Authority:** Governance holds definitive "stop/go" authority. They utilize RACI (Responsible, Accountable, Consulted, Informed) matrices to clarify decision rights. For example, while the IT delivery team is *Responsible* for building the model, the Governance function (often intersecting with the client's Risk/Compliance team) is *Accountable* for compliance with data privacy (e.g., GDPR, AI Act) and can halt deployment if bias or security risks are detected [cite: 23, 31].

### Change Management and Adoption
Historically treated as an afterthought, Change Management is now positioned at the forefront of the engagement, reflecting BCG's 10-20-70 allocation where 70% of the effort must be directed at people and process [cite: 1, 32]. 
*   **Placement & Reporting:** Change Management Leads operate alongside the technical delivery leads (Enterprise Architects) but report up through the Business/Domain Owner or the Value Realization Lead [cite: 4, 20]. 
*   **Authority:** They do not own the code, but they own the *workforce redesign*. They possess the authority to delay a rollout if organizational readiness assessments indicate the staff is not prepared or if the AI literacy gaps present a risk to ROI [cite: 11, 20]. They design the "hybrid human-agent team" structures [cite: 33].

---

## 5. Approval and Stage Gates

Enterprise AI engagements utilize strict, gated methodologies to prevent the chronic "POC proliferation" that plagues the industry [cite: 7, 34]. 

1.  **Strategic Alignment / Budget Gate:**
    *   **Authority:** Executive Sponsor (Client C-Suite / COO / MD) [cite: 11, 12].
    *   **Timing:** Pre-Pilot / Ideation phase.
    *   **Function:** Signs off on the budget and verifies that the proposed AI use cases align with enterprise strategy, rather than just being technological novelties.
2.  **Ethics, Data, and Risk Gate (Trustworthy AI Gate):**
    *   **Authority:** AI Governance Manager / Compliance Guarantor [cite: 16, 31].
    *   **Timing:** Between Model Development and Production Pilot.
    *   **Function:** Reviews the model against fairness, transparency, and security frameworks. Has the absolute authority to stop work if data privacy is violated or hallucination risks exceed agreed thresholds [cite: 24, 35].
3.  **User Acceptance and Business Value Gate:**
    *   **Authority:** Domain Owner / Business Lead [cite: 3, 11].
    *   **Timing:** Post-Pilot / Pre-Scaling.
    *   **Function:** Evaluates the MVP (Minimum Viable Product). The Domain Owner signs off on whether the solution solves the actual workflow pain point and meets the ROI/productivity metrics defined by the Value Realization Lead [cite: 11, 36].
4.  **Scaling and Architectural Gate:**
    *   **Authority:** Enterprise Architect / AI CoE Director [cite: 4, 29].
    *   **Timing:** Moving from Pilot to Enterprise Scale.
    *   **Function:** Ensures the solution can be industrialized. Stops the release if the underlying infrastructure, API costs, or token economics are not sustainable [cite: 37].

---

## 6. Team Size and Phase Variation

Engagement composition is highly fluid, adapting to the lifecycle of the AI transformation.

*   **Pilot / POC Phase (Discovery & Build):** 
    Teams are typically small, deeply integrated "pods" or "squads." The IBM Garage method explicitly utilizes agile squads of approximately 7 to 10 individuals (adhering to the "two-pizza team" rule) [cite: 13]. A pod usually contains a Product Manager, an Architect, a few Forward Deployed Engineers, a UX/AX designer, and a Subject Matter Expert [cite: 14, 38]. The focus is rapid iteration and proving viability.
*   **Scaled Rollout Phase (Industrialization):**
    As the pilot proves successful, the team size expands significantly. The engagement shifts toward a federated CoE (Center of Excellence) model [cite: 29, 39]. The technical team multiplies to handle enterprise integrations across various business units. Crucially, the **Change Management** and **Organizational Readiness** teams scale up dramatically during this phase to train hundreds or thousands of employees, redesign roles, and monitor adoption metrics [cite: 1, 39].
*   **Run / Sustain Phase (Operate):**
    The consultancy's footprint shrinks. The focus shifts to the client's internal AI CoE. The engagement team transitions to providing Level 3 technical support, continuous model monitoring (observability for drift/hallucinations), and periodic governance audits [cite: 30, 35]. The client's internal HR and line managers assume permanent ownership of the ongoing workforce redesign [cite: 25].

---

## 7. Firm-by-Firm Differences

While the overarching goals are similar, the structural entry points and terminology differ distinctly across the tiers of consulting firms:

*   **The Big Four (Deloitte, PwC, EY, KPMG):**
    These firms leverage their historical dominance in audit and risk. Their engagement teams heavily index on **AI Governance, Risk Management, and Compliance**. Deloitte's deployments prominently feature their "Trustworthy AI" framework, installing specialized AI Governance Managers to evaluate fairness, robustness, and regulatory compliance [cite: 16, 28]. KPMG similarly focuses on functional transformations (e.g., Finance Transformation Leaders) driven by strict data governance and regulatory awareness [cite: 40, 41].
*   **Technology Integrators (Accenture, IBM, Capgemini):**
    These firms excel in massive-scale engineering and operationalization. IBM utilizes its "Garage Methodology," which physically or virtually co-locates business, design, and engineering teams into agile DevSecOps squads focused on rapid MVP delivery [cite: 5, 19]. Accenture emphasizes "Process Excellence" and "AX (Agentic Experience) Design," deploying AI Transformation Practitioners to deeply integrate AI into enterprise cloud infrastructures [cite: 17, 18]. Their teams are heavily skewed toward technical delivery and platform scaling.
*   **Strategy Consultancies (McKinsey, BCG):**
    The MBB (McKinsey, BCG, Bain) firms enter through the C-suite, focusing heavily on strategic alignment and organizational change. BCG champions the **10-20-70 rule**, explicitly staffing robust change management and leadership advisory teams to address the 70% human element [cite: 1, 32]. McKinsey emphasizes the empowerment of the **Domain Owner** (an N-2 or N-3 executive) to drive end-to-end P&L impact, viewing AI transformation as a business redesign rather than an IT project [cite: 3, 4]. 

---

## 8. Chronically Understaffed Roles

Published evidence and analyst literature consistently identify a structural failure in how many AI engagements are staffed, leading to high failure rates (up to 70-80% of digital/AI initiatives failing to meet expected outcomes) [cite: 7, 32, 33]. 

1.  **Change Management and Adoption:** This is the most frequently underfunded area [cite: 32]. Organizations allocate massive budgets to LLM licenses and cloud compute, but fail to staff teams to guide human workers through role transitions [cite: 33, 42]. *Result:* Employees reject the tools, workflows remain identical, and the AI platform becomes costly shelfware [cite: 14, 42].
2.  **The Business Application Layer / AI Product Managers:** Firms often over-index on hiring data scientists and technical engineers (the "model builders") but understaff the roles that translate business requirements into technical specs [cite: 6, 27]. *Result:* Models are built perfectly to spec but solve the wrong business problem, leading to "POC Proliferation"—dozens of successful pilots that the business refuses to deploy [cite: 7, 43].
3.  **Runtime AI Governance:** Governance is often treated as a static, one-time policy document rather than an active, staffed role overseeing dynamic "runtime" environments [cite: 6]. *Result:* Projects stall before production due to unmitigated security, privacy, or compliance bottlenecks [cite: 35, 37].

---

## 9. Evidence Quality Appendix

To ensure the defensibility of this modeled engagement team, the sources utilized range across a spectrum of reliability:

*   **Strong / Concrete Evidence:** The most verifiable data regarding specific roles, decision rights, and daily responsibilities comes from live job postings from the consultancies themselves (e.g., Accenture's AI Transformation Practitioner [cite: 18], Deloitte's AI Governance Manager [cite: 16], Databricks/UHG Value Realization roles [cite: 44, 45]). These explicitly outline the expectations, tiered reporting, and functional ownership of engagement team members.
*   **Moderate Evidence (Thought Leadership & Frameworks):** Conceptual frameworks like IBM's Garage Method [cite: 5, 19], BCG's 10-20-70 rule [cite: 1, 46], and McKinsey's Domain Owner concept [cite: 3, 4] provide the philosophical architecture of these teams. While inherently promotional (capabilities marketing), they are widely accepted practitioner literature that dictates how these firms organize their client-facing narratives.
*   **Thin Evidence (Internal Leverage Models & Exact Pricing):** Claims regarding the exact internal hierarchical leverage (e.g., the exact ratio of Partners to Senior Managers to Associates on a specific AI project) or granular rate cards remain obscured. Aside from isolated public sector rate cards (e.g., Accenture's NASPO cloud infrastructure rates [cite: 9]), firms protect this financial data as proprietary trade secrets. Consequently, team sizing is modeled based on agile best practices (e.g., "two-pizza" squads [cite: 13]) rather than leaked firm-specific financial models. Academic literature strictly dissecting engagement team composition is sparse, though papers noting the relational governance between clients and AI suppliers corroborate the need for strict SLAs and ethical sign-offs [cite: 47].

**Sources:**
1. [boyden.com](https://www.boyden.com/media/how-c-suite-leadership-and-new-operating-models-are-driving-the-51202958/)
2. [bcg.com](https://www.bcg.com/featured-insights/the-leaders-guide-to-transforming-with-ai)
3. [mckinsey.com](https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/building-the-ai-muscle-of-your-business-leaders)
4. [wsj.com](https://partners.wsj.com/mckinsey/leading-change/ai-wont-fix-your-business-here-is-what-will/)
5. [umbrex.com](https://umbrex.com/resources/frameworks/project-management-frameworks/ibm-garage-method/)
6. [alicelabs.ai](https://alicelabs.ai/en/insights/ai-operating-model)
7. [substack.com](https://carlotorniai.substack.com/p/the-false-choice-in-ai-transformation)
8. [github.io](https://leehanchung.github.io/blogs/2025/09/05/ai-transformation-sdlc/)
9. [amazonaws.com](https://s3-us-west-2.amazonaws.com/naspovaluepoint/1681146554_Accenture%20-%20Price%20Catalog%20(updated%20April%202023).pdf)
10. [myworkdayjobs.com](https://dynata.wd108.myworkdayjobs.com/careers/job/remote--usa/vice-president--ai-transformation---value-creation_req13757)
11. [helium42.com](https://helium42.com/blog/ai-implementation-roadmap)
12. [aitraining2u.com](https://www.aitraining2u.com/ai-shared-accountability.html)
13. [github.io](https://ibm.github.io/data-science-best-practices/project_team.html)
14. [ishir.com](https://www.ishir.com/blog/341480/why-forward-deployed-engineers-need-industry-context-to-de-risk-enterprise-ai.htm)
15. [ibm.com](https://www.ibm.com/think/insights/ai-at-scale)
16. [deloitte.com](https://apply.deloitte.com/en_US/careers/JobDetail/AI-Governance-Manager/364234)
17. [accenture.com](https://www.accenture.com/ph-en/careers/jobsearch)
18. [accenture.com](https://www.accenture.com/cr-en/careers/jobsearch)
19. [ibm.com](https://www.ibm.com/garage)
20. [oraclecloud.com](https://ejhp.fa.us6.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX/job/2618395)
21. [accenture.com](https://www.accenture.com/us-en/careers/jobsearch)
22. [deloitte.com](https://www.deloitte.com/us/en/insights/industry/government-public-sector-services/chief-data-officer-government-playbook/2026/chief-data-officer-ai-governance.html)
23. [europa.eu](https://www.eulisa.europa.eu/sites/default/files/documents/ir-2024-11-lvdberg-hverdickt.pdf)
24. [deloitte.com](https://www.deloitte.com/us/en/what-we-do/capabilities/applied-artificial-intelligence/articles/trusted-generative-ai.html)
25. [themindfinders.com](https://www.themindfinders.com/2026/03/11/from-org-chart-to-ai-ready-how-to-redesign-roles-without-losing-your-best-people/)
26. [accenture.com](https://www.accenture.com/my-en/careers/jobdetails?id=R00351588_en)
27. [aiassemblylines.com](https://aiassemblylines.com/post/how-to-staff-ai-center-of-excellence-enterprise)
28. [deloitte.com](https://www.deloitte.com/us/en/what-we-do/capabilities/applied-artificial-intelligence/articles/trustworthy-ai-governance-in-practice.html)
29. [stack-ai.com](https://www.stackai.com/insights/how-to-build-an-internal-ai-center-of-excellence-(coe)-roles-processes-and-tooling)
30. [agility-at-scale.com](https://agility-at-scale.com/ai/people-change/ai-center-of-excellence/)
31. [digit-ai.fr](https://www.digit-ai.fr/en/blog/roles-responsabilites-pilotage-ia)
32. [exceeds.ai](https://blog.exceeds.ai/10-20-70-rule-ai/)
33. [businessplusai.com](https://www.businessplusai.com/blog/ai-workforce-transformation-for-saas-building-teams-that-scale)
34. [mckinsey.com](https://www.mckinsey.com/industries/financial-services/our-insights/jpmorgan-chases-derek-waldron-on-building-an-ai-first-bank-culture)
35. [automationanywhere.com](https://www.automationanywhere.com/company/blog/automation-ai/ai-center-of-excellence)
36. [aiassemblylines.com](https://aiassemblylines.com/post/how-to-run-ai-scaling-gate-review-pilot-to-production)
37. [cio.com](https://www.cio.com/article/4208076/what-successful-ai-centers-of-excellence-actually-do.html)
38. [medium.com](https://melrefai.medium.com/ten-success-factors-to-establish-the-perfect-ibm-garage-squad-b6116d962a39)
39. [hiddedesmet.com](https://hiddedesmet.com/creating-ccoe-for-ai)
40. [nysac.org](https://www.nysac.org/media/nexcgyty/genai-discussion-for-nys-conference-may-2-2024-final.pdf)
41. [kpmg.com](https://assets.kpmg.com/content/dam/kpmgsites/cn/pdf/en/2026/08/ignite-the-future-of-ai-transforming-industry-through-ai-integration-and-best-practices.pdf.coredownload.inline.pdf)
42. [trustinsights.ai](https://www.trustinsights.ai/blog/2026/04/the-10-20-70-rule/)
43. [medium.com](https://medium.com/@maruthis/ai-shiny-object-syndrome-why-enterprises-chase-hype-deliver-nothing-b0370d3e90ec)
44. [databricks.com](https://www.databricks.com/company/careers/go-to-market-/ai-transformation-leader-7803651002)
45. [unitedhealthgroup.com](https://careers.unitedhealthgroup.com/job/eden-prairie/vp-ai-transformation/34088/98520590320)
46. [bcg.com](https://www.bcg.com/capabilities/artificial-intelligence)
47. [researchgate.net](https://www.researchgate.net/publication/362938575_Formal_and_relational_governance_of_artificial_intelligence_outsourcing)
