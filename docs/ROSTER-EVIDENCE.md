# Roster Evidence — how tier-one consultancies staff AI transformation engagements

> Source: Gemini Deep Research Agent, run 2026-08-26. 17 grounded searches, 47 cited sources.
> Commissioned to answer one question: what roles actually staff a Big Four AI transformation
> engagement, and what decision does each own. This document is the evidence base for the
> role registry in `huminloop/roles.py`.
>
> **Caveat on links:** citation URLs below are Vertex AI Search redirects and may expire.
> The underlying domains are named in each (bcg.com, mckinsey.com, deloitte.com,
> accenture.com, ibm.com, kpmg.com, europa.eu). Re-resolve to canonical URLs before
> treating any single link as a durable citation.

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
1. [boyden.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFDH1NWsLH2ZIUTpswy1IhQDRPbobhEnXNNB7xPqOLG8D4hx9TFJWneCfYSyq4l9p-UBdOdNN8nMYNBGC22wNkz5C5l07cHYu_gFFPeMojV7gckkWSYfAtygNw5hvLEPNzuxjgvJdI7RxagI1rgSQOMq4_N4rxD38y9uy8vraHX_0prAvCMqx9PzaeNjgxOsbcGH4KVKz_vw5JCWGE=)
2. [bcg.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFRrQTy-VVZVuwbWUDTMVhV0CHFjas9bWVdy_O35II-R2Z2YbXSrqNrx-9WDzOn5jQo2GsQJNGcURiKYWa5EQfoctKCsFhD98SaLJboLRBwgs-ksbKRFbu6M4hX1qOHMtcV2jE1eYxk9uVXq2Rp3jCz0fpfEQ6ZV3FfhGB94Hbrh_O7aMXk)
3. [mckinsey.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGzSAyF5-tIrEdFFcDbsWAXUxOUpg5wnsHURY0_lJKdQVJtYtD_jlqHXQk2CLDNPTho7X5TWHZvVP0iUInEkJunb1SS6wfC-S1PzNYA2A0ZsLXSMXeBblxGxIh8NFpnE3GuRGrEP_r0Bu_r6iM3nVmzdyVmPK9RxoCtDk_BGFz5gmhAFRJWcCi9LNKTuhR_b1UW4PxPVdUPW1d4jJh-6SmeRjb9cQ==)
4. [wsj.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEgkbenVC2yZ9edA7lnSnbLilxiMToO-LDYIX4TyiGzNKPRuJPsb2hE42F1lyF2-FIlxj5gSJe3RAio6C5LLcbo7YEZEQyQivy4EQ_yz7m6bxsNgYGmoXNApLJ7eClA6U4VpDHroFPN_4Fn1HxeRMNjx3_dJzkil6payskJ55tXxvVvClN7HlGWzv1myep-DRaq7So=)
5. [umbrex.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFCroQtjyE4UAvUj7eKhCaui8tJ-lqloKwmVWPrbAluZDpKTrKftTJwpv1fPKZlGpvfLdsqLOuNqm08TdgFmWc_MlbGVyoelUkOVxfMnGA9KIsKQ6CZJ488fHY8WpL8k8dmotYunJkoyzTd14t-zFnsxAZsOAj59jozGZjIl6ktRtLi9ywS_jp2NcmEIiAX)
6. [alicelabs.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFbSczycSrJ5nivKeM5qYXbF5T5XgtLsobba7b36Dp0dOwFM5Vli4D84LaODNR2I9glV_OQx7-P-hsWekR-FqMSWzMx-QsmDTAnzD2OWr7xolH5ruskdu1j2cL26w3D7mI3GduHz77IyLY=)
7. [substack.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEOoSB3TGAweABXmdXlokFUhESK_fhr2SfQsiXIe3m7-LOqH_cnU6i2tvVZGz5GKlivIb1plQwxqSc00BBLoSsl3SVdSnLRV8hUkZJQxx7NSsbeKAAd0jYt3YM44YPeDqrUX50xajGrKX8Ycqp4rz_KkQegxqkLX9Y3xTpBUr6x)
8. [github.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHT_KsSxg3C6ZWV8LGDruCaLzI16AqrbR4NRmks-LSb1kN9AAZpKkYRcABXRxb0vqKuVR4FV6ghNGsahMB_bCJz5PuGKxtz8OUwSAqyrEMcsDQshhrNNeD5lW8KLGoyQvSW1dRyJ91KNGSmYqPC5n73amF0Svqwj1XBgLEZ)
9. [amazonaws.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGPjWVfn98l-zksq1Katrnmx7vE6eYRHTiUA2A9fLkYDXKIVHakphUvTmyS7Z1ehKXJMgVZjl560AEyyaBySmKF3Ju8VVxE9Rk3yBH4N5l5dDwrC1QxU_KKQaoFSpeIbqQw2JPfJMb1rUBIbt8TjH-gZTBVgTxfR_Dc8d3CvjCiP2uhcyEQ1W2DciLHB43YN0kf_DBbUJ7wnH2uRcr--caM-cpov_glwg4MmJqHcyh_pSB7)
10. [myworkdayjobs.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFvJ4E20jTAA3bn6ySrwfp-x6eXtsn3RTBzm5x3WSgFhmPglZe7o9I0lvyQSsvAOh0OQPRoAsbQCpI9VO_aNR5FcPMN_fEfANyA_ypPsj7Fw3PEfGPv2wBMvX5YuN5g8kN1OtR4KrF9VlwPGsQO_lAAHz6bJMVNX-9v2cPNalO3McSeVI1JtxEcEYc4i6gJiSJ9Tt5SZAti1l3SQ7-qTtzO35imcr6DkTthLtCeA8_EDg==)
11. [helium42.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFD3EiYou_10H07b2_k3RFRcCk8ha-SyfkwBDMyCiLa9jEdv3NjRs5OmZvY-aGtbmI4Up-Ih59Ov1JwnuBcwj6NMrrC0vpuKbPN5uPAPPEfsKihFMrVqA4Bgr-Ry2eYV8cCLxWasNHarAU=)
12. [aitraining2u.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHJLZD2-BMEw7puSvO9GoNXvP_2pO09_drsD0_1bkQsRfDPH20n1yiJeXA_Sxe-JoaCFWlRiABgk8QDJZUL4tyGg9iBj6bQqbL5FUSAohOP3FICCMBUZ4NTfQYcHuPmu_CiMHBv_Mmo4OsAaOIgnRWL)
13. [github.io](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBsNnY-gKD-s-fJcF93G-L_R9tXamtBaDMCOJRMgbhbebVnIUmGVzOZPumTvf8VcjqiY1jKg9Pp9MLGdENcDix7Rkjy9TSyroHdXS5D2ky1jF_aaSkEMZddU4UVM6B1RsZbph-qC-5f5bxaZTP5mVll0doNM7coRye)
14. [ishir.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHa4rkC0dLe4TjGYYPwLPpqsmvG_QWVgbtcIfzaf5XzrHdvbo8-K4ajJSbyhmwcK4qeLwQjYjx5sGwVRK0Eoc-WeFEy6AJO6tb6Tf9uFe5tip-mJPdPxyMdbaUg5GJwGOk8mJYSu3CUlONLYzdfyYtT4zrj09mh-98XLCBsVnXMbhxZ8AyWEbSuNcFmn9QFSbyr9jZI2jipwwleChAl2ATWVTRjBegSmney)
15. [ibm.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGYuVttQIs-tqrniiBep0-FtnuTJuIKXF7eBoDEOih1uLUfHrI8HK0HpJ-wncb-r0ZGy-sV0qMAvciUDAz7BxlLFZO_kQWVhK2Z7jaAk0FNp3d1dmJdlUAoZDoNQg-A_3XPSsHc)
16. [deloitte.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGnmr2y3OR7ALXzY5tXEKOnWzNv_qfazmhM1jkNqUj8h3mNxk8lappjjxMNyo4krFo0xUrw8MOZ1VdWD1iU6iBLLq8uf1SIujp6zTdGO9Z7pMtRFXc6ou8jtEzbHFF5m5i9t_OBgaRKGQuHVRcFne-Mn2VSl0Ehk89uUpgfXX9g_z8CjGc_)
17. [accenture.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGd3O2bOqeAsjyxRI1rnWL_Y5ap3uKzlzRPj0CV0kNyGGz7_htF8vxaSJtzXbmTh4zjicwfxDrJszAAm2F8UPANHuLPRGqQfLSa_Sc1MEaRTx3wlbm1Dmr6BkiijzOlYdXkC6MpyGDl5BFnJqMdksFi3HGJFjTlkS8=)
18. [accenture.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHYYfOgVXSSIaoNNlEJeZeIwdYZ8rrf95VqSYSJauRTrSJHoYf_wwgZ0EfRuwau0tUxoXCNHyCMHYmuf_MYNt9y9NX5Pp2VVPM9RJn44XPmlIwEVNwRNS_TVMyS9rTt_YBMa-3gZ594sVs-wdyBa9d7mEum7jrSfpEv6y0XujjttvKWOL8=)
19. [ibm.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGgWy91JjBghq35FYIgyLj997YcBqrUvfT3t3UIHG6fLR8vl17PwI_iugtOBzmvNCHFB9XGCghCRo20RSXKnEgyabTxLPtFlFzLDwxlLuP0tQ==)
20. [oraclecloud.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHuTptChSJe4oTR5F2cZSrfMIyiMfBZP5FKdA8a3jdFYCBUXHyh-ByPJnxY0GM6Tf8l7rddr3rROLTDBrtq19cYLHy4mbvsIHVbAF_UdlmtmFN1LdV6s3NoZeNXQo6XmBQUjVQL29rvnQBPoCp9z1kBf-75dPjedeHBX5sSHIfzYOhtdZq_VAQUmzD7)
21. [accenture.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQF1R6sIfhozp_fiwzdBZJpJ3_iuT6eKv2Xbg4nDxQTlq16b_OXZ4XGW3D9I8MKV3D2mzLbSkw8fx905ACjseLc6iCYOLyuerbaRJ8XF7iEzjWr88apF4VDkPjfDJc1bVjMxXaXf5t4o8P3hkTFW__tEwD39NH-OE9A=)
22. [deloitte.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGO2vD12tKyy80QHpRqSx00oF8Z-dQAorCuYxkpUWiF8-4DsLwNRMJnTY0NTh_c93G7Uys46if7yQHGNUmSGkiV9CwBlLbolfkKA6yx2BS6lc8_DvDEhtJWf8_aai6XJITvagmhDhBeeLo0XFvLZXj6aMhs3FZA68BaP_RN6V20y-o6nVhbLgzQezhqUqeZt4l17JnYXEQ4YcwqWy54QnBT9mB8p9q1DfHwa7CQ0DDSWEqWNa54g1t_Qi91pflUX5k4AASGO-dneWJlfN93ooB4xbXO8NoLU8qavMY=)
23. [europa.eu](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQH7mks6JyQW5J8cyq3wNWVlN0grpRLJCDfo2_PNrqnd7mbmRXSlVf64ZRkTGhkRGGbH5ABj5f5WbwwlFPquJOHDZKTcHqqoEDBDsjaCC9YDoJOoVFEM7OqTt14sIckI4Y6X68d_dfEPbS0Qzecgrrk3xw38csULGwDkKVhyyR4RUU65nZIcr_A-JzVghZyf9PzZ)
24. [deloitte.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFm1mJqJCg6BKctNlnVY7SxnCIlKjlTaeq_CR7AJWi4pu_lCkcbegoBLDP0YDj-9RuXZNuB1sBLdjB3qXe4MfD1D8G3h2t8VZ23u-DY7H_msd5wIO9-AOoo7JqdO2YNy6uMXE_eK3Xty7sQeaDu9fn3mnLE1i-BLPQVKd58mk6bNoBEGz5qGtyBi-kbpocMjUU6bqZOscn13sTQkL8Jncg_OXa_7sBxEZAMk6Us2g99cQ==)
25. [themindfinders.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHZGa305dbIBNXPF6pD0d6tF-KiZUKuPVHtBTAlAlY_nK5RMumsJte86KxDDO-FPdMc0qvZ9qafAtoeMiDphYwpKuCAgVXEUD4_htCXJwRyqbsSsZ-M2rwmRPcMZ3uV9H6F_F6ptO3TQmUBH7pttbHddgLBT1DHt0gIxwubQZdwxwbVYMm291NQSkegelMPq18BfyYwh-rKYZ-pd6YgrdP2RZHdB2eg1kP8BlZ8T7syjb0=)
26. [accenture.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHil3C8_7l7ZgY_vUr_-v94o0Nb5Fm72zem4NHz9vF-M5frjG1MMmd2RXzi07ZPEeudihJFNnOwl9QILaUJurkM17kG_NXmF7b3XK6f7VE1xQGgr5ybLo7zAquK0OwU6CeQIyWED6Tl_7pWXvcnaFupgrl5nQ==)
27. [aiassemblylines.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHUWl1eg5hsgUPD2e7VTdtaFiIkgLiFGSw11LBErVY7PzZ2v9WHpLeLAFxYOKkQs4Yth6WiaXuEg7nGZA_E7JFSU-oAnxhzT3Xc7sIZN3XpyiVsL-hsY6GxEvKuy9aPEsNHacoU1NDfs8r2Zyr0x9RW5d44IdtCL-NbmCI99CRMtASIwPrdcA==)
28. [deloitte.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGji1DgKqXQx0e3GDeLIlp_GIv7dKbIOddMKXd9I9clqbW7d-6yRJo3-G5Z9F6pDziONp3AmXLWpfuc1KEhWFtm9TZ3-NmEOjBQApR3fqDuZzN3zDahEhCFeJRFk6XfFVPm_inakRweCcLMaqMA375C88l-dqqAmCUvhXOPYQBaNlctovJU2G_l23x2eYlFBKscktYYUx4uNp-2bA2V81irRH921R67bS6mqnSi9UHRcyEqjdwJdMkyEHOS5JUXhINE)
29. [stack-ai.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHTwA_N3ZQAWiWG-BZXRDnzKDu2S91vhHWKJiiERMSLkf_1QdL2gWqW5PpkxOEXQ-oCCNNyRF7T3W_kBHdtI4H-95XOVql-ax-jJ9W9kr-kXeDzc4FNHrQ8idY8X4UhHMzzi8Flcc45t-yFoy_Dmd7Vwr7UAL-Aw5Wjy2x6lPM-Kec5kihJyhFB0hRIbCC7b4u_czB6IIr1lKTZZiT9aNmpdVsyJnDbd361aw==)
30. [agility-at-scale.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFHZxQqjl3ez3D0nvHSjCe8Ldil6d9ajKOQAerGXTJXDehAi2APGGyR3k8bcIN9I-hzOKYe6Id6N0l7scdkXXJFHJITjsCPZa0r1OtOXtAV144clQhpbGaDBNM9REW2PYVRxH2bh_LsuV5jRK36eBSCiCoQokDdkf3Psiim)
31. [digit-ai.fr](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGdIkpyWjs8pyWwfGw3N629ues6og5HbHHJICL8ebABzIV2cztsy2eRYLqPFYoXjv3BTj4ksPwFtJwUjNwu5zG2rRZB9A3sMWEWwlNO7Q738cCsb2jxOmf3rtq7Gr3XVpptVAiwTTU2oXqCWhAN6x8pQ9cvgJoN7Q==)
32. [exceeds.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQE6Ydn4w4LS1-I4PcokTWcsPKBBhspJBTwXP58WV5QhOqqzbkpNGeIXgtp-ub4t2rSDs9gsuXMQnW76AecBT20N6GsDS4zHN9FBTzRHVCKShoGcvfhFrRc-OPmmtEY-xg==)
33. [businessplusai.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGkZYFHPYYIDg5IKaaG5HLdpeKFuHHZhVgXXsW-JKJHn4EC8m_ZTz0AmNaIObghvGJHLx-LI9IuOFulh4T9_LdfHWChUBTwxhmvMQ9R1Bi1ORajTxu3lE52D5q3OwiiJkaP_rhEgXnX8oBgX-xDvumr7d1J9ndS6Xc5JK9TfrwQAk-VEtza0Fnl4agOYmSNQpAlFXmr_O4Opg==)
34. [mckinsey.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHrCbeRr3byApheOAwKsMG_UzOiagAP1Ib20dR0PjLH1BSlb0ypOVqEnxF8X3dU0AyMF6DCHViNwpwS55lXpCqXT5K-8OoNpBMwD8cyYVBWTnIEjMtjfBZRDgtKrV9rj7YxxyIwhPI0cDXxHZbidfWsaNaOq78RqwM5stLHkfeIxnRO3ZftbaUa8kVWJxJ3Xo0S0mm33XxkBtJPHxR1nbQNfbZ9hZ7ODEB1qiWheFymc6MxZf13WyOfsDBfxf0=)
35. [automationanywhere.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEJYXOaz6P40RlAVW4UnE9Xx4xas_7rLvwVbQMa3Oz5PS66UP0gBOnHPsyGRQI2ZHJZ_xpNGOLS8qHaIAifcDp_prfeW3XfcEOnqrN7bSoN7OJ9gMKJSfNej1x3oTKR-bxlSWPKGD6EHq2Dv6oljZMTyB9HQ4HzhXuVJ4SCSUHLTed8Oh3T0hqdzRPW)
36. [aiassemblylines.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGDmk6TsIsfpWea-aKrWpbMqRGUVm1zFHpxxCiEcfJzSbL1a2WoTLOzM_0AH7FiMYSdLYtGvN-os1JusFq8vxOtts1FQ5LeKwaLBiybq2gPo598PZdyP38gKjLOHsKk-ZBPsK0vQ_toPWLjFQXbHF5O404uIx4b7FtGC7Wn1VI9HetS82RTepVX0kvMBw==)
37. [cio.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHL9YehvqdsOaQ_G5IJaeL1ZSqAIpzWJ9Mo73BUdThadFYFCKxrkdKrLBOj8WVk09kyixPTSOToeAKGkeya-wFnow_bzCQw7IEOO6htAbK0h4cg4zyh3SQbnbYP0NUkCp_IlFBWcRtHc7LNK9URoT-zxylozeNUKcjvvK1hF7_9Db7adhMqu_CIpWHuTSjmf5keEi8=)
38. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEDGkJPYMJ_CdwLo9brlYUwyn7V_wanGzsEdl5ovBi7fKlLLR3o7pAhxSc0eFRuUQFH3WloCc0ULfX2sgFWj7T9Oj_ZfDsqa_TOZG9ScADYA5ZLpT4rXjuFfv2AotvOV_lVft9RrIsPGxXkU7Nr1pDDdG2IGqc8DSpEGTv43wkKzm8mitSFy22WyG5MMgIHBevbm-QFyEjAvWU3MTY=)
39. [hiddedesmet.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFpvlriwS9nyFuRccAhhyb3iTNctxfUyE--PBh3OvyrP3fFDt0_zSylhwIXlP5VhQ2WLpZLgTWQjTllEvHWdxi7dJ1gJBbgX6w6bV-kR_qOmyS8gGxG87KKpkJ9xmYTN28xxw==)
40. [nysac.org](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEBrE-KyP9DBXe09a4faKpn9AbNnoQcSqmHsG-T2AkOZZs8uT14ApcePF4h4X4AMn0aN_TV2cA1wu86reDGj2lRlOPmvpEfxBJBnFHVGY5qnGsW9_aBkajDaB2zF_GkzT6qmeI5YxR0iFrWqXYmytJJZExlqE6zgtriJZH0jFuA1iGC0nwim7XEHFFI2SMOdYdWWHo=)
41. [kpmg.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQEEy4bz4A_FHknniaOxPGDAvW6ejaivseB39Po6HpFo5iIR8FHb-BAEjZ69YKPtG-98nyo93gOeUQtnKjHqAbdBd_ZdJTJ7Am2Zg4Z88n_RY7eNWdrdxbDZFmCREtoyPXtD0FO-CFPRI93Ph5LvTPhpnYOjZuPk57HG2OhD8YFavWRfZXsoPQnIVo7TVofJx1whdoOCghiA7mEXghkQhvvcCRQFd0iOJETg3eK-eiSeVCt7jL0uINgah_KLYscXoK5hcjqaEV63-OqJfRTLHP3QMGm6yxjcaO07tiLvcQt4ZujPUisJkEqaO-U=)
42. [trustinsights.ai](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGUbNHbexGYdJR6zF2IJmmN_RKSUZ-Ebl7mBVJC_dlX-5KBWpNqTn7FAtMJ87ZYrQF-or52MvX8EE6UzcfloaRd5lJdD7UN3KTuPM0u1mMMCOfBJFpJIsbSmI_1M3qT713ZJai1LLhSiuY6qgkiHGobfFc=)
43. [medium.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFuhbWuULHIxOE6YjoAxmx02PgbNTbl4OrrRIxx1UeXKkD2_azyxFlEAif5AkIf2tRKATBzXmnUHkaKcZR3t0h6k__pxqjFvkYkhEz0Fkhfvad5oGJaL4T4gCuB6kGECc2bs4W66Pwkubj_c2c4_nsoCiSmtXoJ8xwPNcC6bFhQlRVweblZy-T4wFpjSikYFH6SQRg_XaKyY8UDChAjnzqL9dNV)
44. [databricks.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGa65MGr5sn8_WYWA1viHFQQic7FdmuRn4ne5MyK8tLpowQqiaiM57GP1XWN7YQKvUCkNt66xsuQAhh1b0yUBGmDCrJUAAJFk1ZLxEpZK0agT_dLHPDrNNiDnWMfy1Gc96SyPtOCAli3rXUBEmLIOWza0h3USVCzq7W8jJQS7ezIEn_slFraaP2rYreDlovLOIS2g==)
45. [unitedhealthgroup.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQHfnMa90RDfHXEFd7LYw1ONr4_ljMGXiH4F0R3pffOha2N39jQlzavnEn_L_ib21To_oQRvIKCnKY0M3speUhnsgGQ5e-OWT__TynLQ0Aq2ZFex2hpOwCbxqmLlrcKwl0IYoPR0iaxfq_onh0lwaT181TDjrpV7-itIfBbQ13hcamfpX5A7u9xnPfxhRrw59a7Vg8E=)
46. [bcg.com](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQGFW4PHPB6Z3n-PRIG_73KJoBHsmEm6d4njottUaDiCdgTq9xB-5jpWoshASLNwGjU2MWcmXYtAOWYujOjXCOiK8WK6X_Zma9Y3c9ICnraJ3VW04R5Aft_YSpWnVpwqoqnGiN4yBdJJE9jK-OIIbA==)
47. [researchgate.net](https://vertexaisearch.cloud.google.com/grounding-api-redirect/AUZIYQFVftlz8NLQIdAcfWUdAqemgfavcKqQDRLb78Wi-qAx_ig5Ue5FQox3v3Tlx3mLVlCqJqiOsOEEMQZib9Sb8dgfbAeREVZtpH3fa9eZ23Cj5P6RRvp35z2UJGSdTvwU0zyOn9QFz__QcQjaLObG75c71h9SMhoFXtxx3ARiFRMxI2kSjJpPm3dKpvj410EaSI2Mf7LBRi6fhDexzdQut3wi8g605Okj-49XhBUMvULrHw==)
