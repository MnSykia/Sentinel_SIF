PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

#### **PRODUCT REQUIREMENTS DOCUMENT** 

# **SentinelSIF** 

An AI/NLP Engine to Detect Serious Injury & Fatality (SIF) Precursors in Unsafe-Act / UnsafeCondition and Near-Miss Reports 

_Prepared for: Smart India Hackathon — Oil India Limited (OIL) Problem Statement Document owner: Product / HSE Digitalisation Team Version: 2.0 (Prototype / SIH submission) Status: Draft for hackathon review_ 

##### **One-line summary** 

SentinelSIF is a standalone AI/NLP engine that ingests free-text UA/UC, near-miss, and incident reports and sits on top of OIL’s HSSE reporting flow. It automatically (a) classifies each report as SIF-potential vs non-SIF-potential, (b) tags it to the relevant IOGP Life-Saving Rule, and (c) surfaces recurring precursor patterns — activity, location, barrier failure — on a ranked, interactive dashboard. It works against any report source that can export or stream text: OIL's current HSSE platform, a future one, or a CSV dump handed to HSE today. 

Page 1 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **Contents** 

1. Problem Statement & Context 

2. Product Vision & Goals 

3. Users & Personas 

4. Scope: In / Out for Hackathon Prototype 

5. The Classification Model — SIF Logic 

6. IOGP Life-Saving Rules Tagging 

7. Precursor Pattern Extraction 

8. Functional Requirements 

9. Dashboard & Analytics Requirements 

10. System Architecture 

11. Evaluation Plan & Success Metrics 

12. Data Requirements & Handling 

13. Non-Functional Requirements 

14. Relationship to OIL's Existing HSSE Platform 

15. Risks & Mitigations 

16. Future Roadmap (Post-Hackathon) 

17. Appendix: Reference Frameworks 

Page 2 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **1. Problem Statement & Context** 

### **1.1 Background** 

Oil India Limited (OIL) operates a Health, Safety, Security & Environment (HSSE) reporting programme through which field staff and contractors log Unsafe Acts (UA), Unsafe Conditions (UC), near-misses, and incidents. These reports are captured as structured metadata plus a free-text narrative describing what happened. Today, this text is triaged manually by HSE officers at fixed intervals — monthly or quarterly review cycles — to identify patterns and decide where to intervene. 

This cadence creates a structural blind spot. Global safety research (DEKRA's Martin & Black 2015 study, the Edison Electric Institute's SIF Precursor / Safety Classification and Learning model, and VelocityEHS's 2024 PSIF classifier) has independently converged on the same finding: 

##### **The core insight this product is built on** 

Low-severity incidents and fatalities do not share the same causal pathway. In the DEKRA dataset, non-fatal recordable accidents fell 51% over 15 years in the US, while fatalities fell only 25.5% over the same period. Treating every report as equally worth investigating — the old 'Heinrich triangle' assumption — dilutes HSE attention across thousands of low-consequence events and delays the ~20-25% of reports that actually carry fatal / life-altering potential (a 'SIF precursor'). 

A SIF precursor is defined (per DEKRA / EEI) as a high-risk situation in which management controls around a highenergy source are absent, ineffective, or not complied with -- the presence of high energy plus a failed or missing direct control, not the severity of the outcome, is what predicts fatality risk. This is the exact logic this product's classifier is built around (Section 5). 

### **1.2 What the problem statement asks for** 

- a) Classify every free-text report as SIF-potential vs non-SIF-potential. 

- b) Tag each SIF-potential report to the relevant IOGP Life-Saving Rule (Energy Isolation, Hot Work, Confined Space, Line of Fire, Working at Height, Driving, Lifting Operations, Management of Change, Safe Mechanical Lifting, Permit to Work). 

- c) Surface recurring precursor patterns -- activity, location/site, asset or barrier failure type -- via an interactive dashboard that ranks sites/activities by SIF-precursor density, so the HSE can route interventions to where fatal potential is concentrated, not just where report volume is highest. 

## **2. Product Vision & Goals** 

### **2.1 Vision statement** 

Give every OIL HSE officer two things no manual review cycle can: the moment a report is filed, know whether it's a genuine SIF precursor or not — and at any moment after, see exactly which sites, activities, and failed barriers are building toward the next fatality, before it happens. 

### **2.2 Goals for the prototype** 

Page 3 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

|**#**|**Goal**|**How it's measured**|
|---|---|---|
|G1|Automatcally classify free-text reports as SIF-potental vs non-<br>SIF-potental with high recall on true SIF cases (false negatves are<br>the costlier error).|Recall >= 0.85 on a held-out labelled<br>test set; precision reported<br>alongside, target >= 0.70.|
|G2|Tag each SIF-potental report to the correct IOGP Life-Saving<br>Rule(s).|Top-1 tagging accuracy >= 0.75<br>against expert-reviewed ground<br>truth; top-2 >= 0.90.|
|G3|Surface recurring precursor paterns (actvity x locaton x barrier<br>failure) on an interactve, rankable dashboard.|Dashboard renders live ranked views<br>for all three dimensions and is<br>demoable end-to-end on stage.|
|G4|Cut the tme-to-visibility for a SIF-potental report from<br>weeks/months to near-real-tme.|End-to-end latency from report<br>ingeston to dashboard appearance<br>< 5 minutes in prototype.|
|G5|Be explainable and auditable enough for HSE ofcers to trust and<br>correct.|Every classifcaton exposes<br>ratonale (matched<br>keywords/evidence span) and<br>supports one-click override.|



## **3. Users & Personas** 

|**Persona**|**Role**|**What they need from this product**|
|---|---|---|
|HSE Manager / Site Head|Owns safety performance for a<br>feld, terminal, or drilling site.|A ranked view of which actvites/locatons under<br>them are accumulatng SIF-precursor risk, so they<br>can target toolbox talks, permit audits, or<br>equipment fxes before an incident happens.|
|Corporate HSSE Analyst|Reviews trends across all of OIL's<br>assets monthly/quarterly today.|A live, always-current precursor dashboard instead<br>of a statc end-of-quarter report; ability to drill from<br>company-wide view down to a single site or crew.|
|Field Supervisor / Filer|Logs UA/UC/near-miss reports<br>from the feld, ofen in a hurry,<br>using shorthand.|A system that doesn't add fling burden --<br>classifcaton happens automatcally afer<br>submission, with no new mandatory felds at the<br>point of capture.|
|HSE Investgator|Follows up on fagged high-risk<br>reports.|Fast access to the evidence that triggered a SIF fag<br>(specifc phrases, matched Life-Saving Rule) to<br>prioritse and scope investgatons.|



## **4. Scope: In / Out for Hackathon Prototype** 

### **4.1 In scope** 

- NLP pipeline that ingests free-text UA/UC, near-miss, and incident report narratives from a labelled sample dataset assembled for this hackathon (see Section 11). 

- Binary SIF-potential classifier (SIF vs non-SIF) with a confidence score. 

- Multi-label Life-Saving Rule tagger mapping each report to one or more of the 10 IOGP Life-Saving Rules. 

Page 4 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

- Precursor pattern extraction: activity type, location/site, and barrier-failure category, using named-entity recognition + rule-based/keyword taxonomy hybrid. 

- Interactive dashboard: SIF-density ranking by site and activity, Life-Saving Rule breakdown, trend-over-time view, and a drill-down report explorer with model rationale. 

- Human-in-the-loop correction flow: a reviewer can override a classification; the correction is logged as a new training example. 

- A generic, documented ingestion contract (a simple schema: report ID, timestamp, site, activity, free text) that any HSSE platform's export or API could be mapped onto -- proving portability without requiring access to any specific platform. 

### **4.2 Out of scope (for the hackathon prototype; noted as future roadmap)** 

- Live integration with any specific commercial HSSE/EHS platform -- no such access is available during a hackathon, and building against unverified assumptions about a 3rd-party vendor's API would be implausible. 

- Full retraining pipeline / MLOps automation -- prototype uses a fixed trained model, with the retraining loop demonstrated conceptually. 

- Predictive forecasting of future fatality probability (the prototype is diagnostic: 'what's happening now', not predictive). 

- Mobile app for field-level filing -- the product enriches whatever channel already captures the report. 

## **5. The Classification Model -- SIF Logic** 

This is the technical core of the product and the section judges will scrutinise most closely, since it is the direct answer to ask (a) in the problem statement. 

### **5.1 Core principle: energy + control failure, not severity** 

Per the DEKRA/EEI Safety Classification and Learning (SCL) model, SIF potential is driven by two factors present in the narrative, independent of the actual outcome severity: 

- **High-energy source involved** -- e.g. stored/pressurised energy, elevation/gravity (work at height, dropped objects), mechanical energy (rotating/lifting equipment), electrical energy, chemical/thermal energy (hot work, hydrocarbons), motor vehicle kinetic energy. 

- **Direct control status** -- was the barrier that should manage that energy present and effective, present but not complied with, or absent altogether? Absent or ineffective direct control around high energy is the actionable precursor signal, regardless of whether anyone was actually hurt. 

Page 5 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

##### **Why this matters for the model design** 

A near-miss where a worker was standing under a suspended load with an inspected, rated sling and a certified lift plan in effect is NOT a SIF precursor, even if it 'feels' scary -- the control was present and effective. Conversely, a UA report describing a worker bypassing a machine guard with no injury at all IS a SIF precursor, because the control (guarding) was absent. This is precisely why a naive keyword-severity classifier (e.g. flagging on words like 'injury' or 'blood') fails -- SentinelSIF's model is trained to detect energy-source + control-failure co-occurrence, not injuryoutcome language. This distinction is also the single clearest thing to put on a slide for judges: it demonstrates the team understood the domain science, not just the NLP. 

### **5.2 Model architecture (prototype)** 

|**Stage**|**Approach**|
|---|---|
|Text representaton|Sentence-level embeddings from a pretrained transformer (e.g. a compact<br>multlingual sentence-transformer), chosen for fast iteraton within hackathon tme<br>constraints over a from-scratch fne-tune.|
|Energy-source detecton|Mult-label classifer / keyword-and-patern layer over a taxonomy of high-energy<br>categories (gravity, pressure, mechanical, electrical, chemical, thermal,<br>moton/vehicle), trained on labelled spans in the assembled dataset.|
|Control-status detecton|Classifer over three states -- control present & followed / control present but not<br>followed / control absent -- using cue-phrase paterns ('without permit', 'guard<br>removed', 'not isolated', 'bypassed', 'PPE not worn') combined with the embedding<br>representaton, so paraphrased or code-mixed phrasing is stll caught.|
|SIF-potental decision|SIF-potental = TRUE when a high-energy source is detected AND control status is<br>'not followed' or 'absent'. This rule-informed structure -- rather than a single<br>opaque end-to-end classifer -- is what keeps the model auditable, which maters<br>both for HSE trust and for a judge asking 'why did it fag this one.'|
|Life-Saving Rule mapping|Once an energy source + actvity context is identfed, it maps to the corresponding<br>IOGP Life-Saving Rule(s) via a curated lookup (Secton 6), refned by classifer<br>confdence on each candidate rule.|



### **5.3 Why a hybrid model, not a pure LLM-prompting approach** 

A tempting shortcut is to send each report to a large language model with a prompt asking for a SIF/non-SIF verdict. This is explicitly avoided as the primary mechanism, for reasons worth stating up front to a judging panel: 

- Auditability -- a prompted LLM's reasoning is not reliably inspectable; the energy+control decomposition in Section 5.2 gives a reviewable, defensible answer to 'why was this flagged.' 

- Consistency -- the same report should get the same classification every time; a decomposed model with explicit taxonomies is far more stable than free-form LLM output across runs. 

- Data sensitivity -- routing real OIL safety narratives through a third-party hosted LLM API raises governance questions that a self-contained, self-hostable pipeline avoids. 

- That said, an LLM can still play a supporting role -- e.g. as a fallback for handling truly novel or poorlystructured narratives, or for generating the initial round of synthetic training examples -- and this is noted as an optional enhancement, not the core mechanism. 

Page 6 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **6. IOGP Life-Saving Rules Tagging** 

The model tags each SIF-potential report against the 10 IOGP Life-Saving Rules. The table below shows representative narrative cues used to seed the mapping taxonomy (illustrative, not exhaustive -- the model is trained to generalise beyond these exact phrases). 

|**Life-Saving Rule**|**Representatve narratve cues**|**Typical OIL context**|
|---|---|---|
|Energy Isolaton|isolaton not verifed, LOTO bypassed, valve<br>not locked, energy not de-energised|Wellhead maintenance,<br>pump/compressor servicing|
|Hot Work|welding without permit, gas test not done,<br>hot work near fammable, no fre watch|Pipeline repair, fow-staton<br>maintenance|
|Confned Space|entry without permit, no gas monitoring,<br>tank entry, no atendant/standby|Tank cleaning, vessel entry|
|Line of Fire|standing under suspended load, in pinch<br>point, in path of moving equipment, struck-<br>by|Rig foor, crane operatons, vehicle<br>movement|
|Working at Height|no fall arrest, unsecured scafold, working<br>above without harness, edge protecton<br>missing|Derrick work, structure maintenance|
|Driving|speeding, seatbelt not worn, fatgue,<br>mobile phone use while driving, journey<br>management not followed|Field-to-site transport,<br>crude/product haulage|
|Lifing Operatons|sling not inspected, lif plan not followed,<br>exceeded SWL, unauthorised rigger|Rig equipment lifs, pipe handling|
|Management of Change|modifcaton without approval, temporary<br>bypass not documented, deviaton from<br>design|Process/equipment changes|
|Safe Mechanical Lifing|defectve lifing gear, uncertfed equipment<br>used, overload|Workover rig operatons|
|Permit to Work|no valid permit, work outside permit scope,<br>permit not closed out|Cross-cutng -- any permited<br>actvity|



Design note: 'Permit to Work' and 'Energy Isolation' frequently co-occur in the same report (a PTW breach is often the mechanism by which isolation fails). The tagger is multi-label specifically to preserve this, since collapsing to a single tag would hide the causal chain HSE needs to see. 

Page 7 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **7. Precursor Pattern Extraction** 

This section answers ask (c) directly: surfacing recurring precursor patterns by activity, location, and barrier failure. 

|**Dimension**|**Extracton approach**|
|---|---|
|Actvity type|Named-entty recogniton + taxonomy matching against a seeded actvity list (hot<br>work, rig-up, wireline operaton, vehicle movement, excavaton, lifing, confned-<br>space entry, etc.), extensible via reviewer feedback.|
|Locaton / site|Resolved from structured metadata where available (preferred), falling back to<br>narratve-text extracton and normalisaton to a standard site hierarchy (feld -><br>installaton -> sub-unit) where metadata is missing or unreliable.|
|Barrier failure type|Classifed against a controls-failure taxonomy aligned to the DEKRA/EEI SCL model's<br>'absent / inefectve / not complied with' framing -- e.g. missing isolaton, PTW not<br>followed, PPE not worn, inadequate supervision, equipment defect. This is the<br>analytcal core that turns a report into an actonable precursor category, not just a<br>severity label.|



Together, these three extracted dimensions are what feed the das hboard's density-ranking views (Section 9) -- a site or activity is 'high-precursor-density' when SIF-flagged reports cluster there, and the barrier-failure breakdown tells HSE what kind of intervention (retraining, equipment fix, permit audit) is most likely to help. 

## **8. Functional Requirements** 

### **8.1 Ingestion** 

|**ID**|**Requirement**|**Notes**|
|---|---|---|
|FR-1.1|System shall accept report records via (a) batch fle upload<br>(CSV/Excel/JSON) and (b) a REST API endpoint for near-real-<br>tme single-record ingeston.|Batch mode is the primary hackathon<br>demo path; the API is documented and<br>functonal but not ted to any specifc<br>external system.|
|FR-1.2|Each ingested record shall carry: report ID, tmestamp,<br>site/locaton code, actvity/work-type (if available), free-text<br>narratve, and any existng fler-selected category/severity.|Existng fler felds, where present, are<br>retained as a comparison baseline against<br>the model's independent classifcaton.|
|FR-1.3|System shall validate and quarantne malformed records<br>(missing narratve, unreadable encoding) without blocking<br>the batch.|Errors surfaced to an ingeston-health<br>panel.|



### **8.2 Text preprocessing & normalisation** 

|**ID**|**Requirement**|**Notes**|
|---|---|---|
|FR-2.1|System shall clean and normalise free text: lowercasing,<br>punctuaton handling, spelling-variant normalisaton, and<br>expansion of common HSE/oilfeld abbreviatons (e.g. 'PTW'<br>-> permit to work, 'BOP' -> blow-out preventer, 'LOTO' -><br>lock-out tag-out).|Abbreviaton dictonary built from<br>IOGP/OGP glossaries + OIL domain terms;<br>extensible.|
|FR-2.2|System shall handle code-mixed language (English narratves<br>with Hindi/Assamese words transliterated in Latn script), a|Use a multlingual/code-mix-tolerant<br>embedding model rather than assuming|



Page 8 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

|**ID**|**Requirement**|**Notes**|
|---|---|---|
||realistc conditon of feld-level reportng.|pure English text.|
|FR-2.3|System shall detect and fag near-duplicate reports (same<br>event logged twice) to avoid double-countng in precursor<br>density metrics.|Similarity threshold on embeddings;<br>fagged, not auto-deleted.|



### **8.3 SIF classification** 

|**ID**|**Requirement**|**Notes**|
|---|---|---|
|FR-3.1|System shall output a SIF-potental label (SIF-potental / non-<br>SIF-potental) plus a calibrated confdence score (0-1) for<br>every ingested report.|See Secton 5 for the classifcaton logic.|
|FR-3.2|System shall fag any report where the model's classifcaton<br>disagrees with the fler's self-selected severity, as a<br>'discrepancy' worth reviewer atenton.|Directly targets under-reported high-<br>energy events logged as routne -- the<br>clearest ROI story for HSE leadership.|
|FR-3.3|System shall support a confgurable confdence threshold<br>below which a report is routed to a human-review queue<br>rather than auto-classifed.|Protects against silent misclassifcaton<br>near the decision boundary.|



### **8.4 Life-Saving Rule tagging** 

|**ID**|**Requirement**|**Notes**|
|---|---|---|
|FR-4.1|System shall tag each SIF-potental report with one or more<br>of the 10 IOGP Life-Saving Rules, ranked by relevance score.|Mult-label -- see Secton 6 design note.|
|FR-4.2|System shall show the evidence (matched phrases/enttes)<br>supportng each Life-Saving Rule tag.|Required for HSE trust and auditability.|



### **8.5 Dashboard & reporting** 

|**ID**|**Requirement**|**Notes**|
|---|---|---|
|FR-5.1|Dashboard shall rank sites and actvites by SIF-precursor<br>density (SIF-potental reports / total reports, and absolute<br>count), not raw report volume alone.|Density view prevents high-trafc sites<br>from dominatng purely on volume.|
|FR-5.2|Dashboard shall provide a Life-Saving-Rule breakdown view,<br>trended over tme and by site.||
|FR-5.3|Dashboard shall provide a report-level drill-down showing<br>the narratve, model output, confdence, evidence spans,<br>and reviewer override history.||
|FR-5.4|Dashboard shall support fltering by date range, site, actvity<br>type, and Life-Saving Rule.||
|FR-5.5|Dashboard shall allow a reviewer to accept/override a<br>classifcaton inline, feeding the correcton back into a<br>labelled-examples store.|Human-in-the-loop is frst-class -- trust is<br>the adopton botleneck for any AI safety<br>tool.|



Page 9 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **9. Dashboard & Analytics Requirements** 

### **9.1 Primary views** 

|**View**|**Purpose**|
|---|---|
|SIF-Precursor Density Ranking|Ranked list/heatmap of sites and actvity types by SIF-precursor density (%), with<br>absolute counts shown alongside so a reviewer can distnguish 'small sample, high<br>density' from 'large sample, high density.' This is the single view the problem<br>statement's Expected Outcome describes most directly and should be the<br>dashboard's landing screen.|
|Life-Saving Rule Breakdown|Which of the 10 rules are most frequently implicated company-wide and per-site,<br>trended month-over-month.|
|Barrier-Failure Patern View|Cross-tab of actvity type x barrier-failure category, the closest analytc to root-<br>cause clustering without a full investgaton.|
|Trend Over Time|SIF-potental rate over tme, overall and flterable by site.|
|Report Explorer / Drill-down|Search and inspect individual reports with full model ratonale and override<br>control.|
|Discrepancy Queue|Reports where the model's SIF call disagrees with the fler's own severity selecton<br>-- the highest-value queue for a reviewer's limited tme.|



### **9.2 Design principles** 

- Rank by density/risk-concentration, not raw volume -- this is the core differentiator the problem statement itself calls for ('ranks sites/activities by SIF-precursor density'). 

- Every AI-driven number on screen must be traceable to underlying evidence in one click -- no black-box scores. 

- Design for a live demo: the dashboard should tell a complete story in under 3 minutes -- landing view -> drill into a flagged report -> show the evidence -> show the override loop. 

Page 10 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **10. System Architecture** 

### **10.1 High-level component flow** 

Report source (file upload / API) -> Ingestion & validation service -> Text preprocessing (cleaning, normalisation, codemix handling) -> NLP classification pipeline (SIF classifier + Life-Saving Rule tagger + precursor extractor) -> Enrichment store (classification results linked to source report ID) -> Analytics/aggregation layer -> Dashboard (web application) <-> Reviewer override loop -> Labelled-examples store -> Periodic model retraining. 

|**Layer**|**Prototype technology suggeston**|
|---|---|
|Ingeston API|Lightweight REST service (e.g. FastAPI) acceptng JSON/CSV, with a documented,<br>source-agnostc schema (Secton 4.1).|
|NLP pipeline|Python service using pretrained sentence-transformer embeddings,<br>scikit-learn/PyTorch classifcaton heads, spaCy or a transformer-based NER for<br>entty/actvity extracton.|
|Enrichment store|Relatonal store (e.g. PostgreSQL/SQLite for the prototype) holding original report<br>metadata + model outputs, keyed by report ID for traceability.|
|Analytcs layer|Aggregaton queries computng density rankings and trends for dashboard<br>consumpton.|
|Dashboard|Web app (e.g. React front-end) served independently.|
|Feedback loop|Override actons writen back to the labelled-examples store; retraining job<br>scheduled/manual for the prototype.|



### **10.2 Why this shape** 

The architecture is deliberately self-contained: no component requires access to, or assumptions about, any specific third-party platform's internals. The only interface the outside world sees is the ingestion schema in Section 4.1 -- a report source maps its data onto that schema, however it happens to export it. This is what makes the prototype fully demoable on data the team controls, while remaining trivially portable to a live source later, whatever that source turns out to be. 

Page 11 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **11. Evaluation Plan & Success Metrics** 

A hackathon prototype is only as credible as its evaluation methodology. This section is deliberately explicit, since 'we built a classifier' is a weak claim without a stated way to check it actually works. 

### **11.1 Building a test set without access to real OIL data** 

- Assemble a labelled dataset from public oil & gas incident/near-miss report corpora (regulatory incident summaries, published IOGP/OGP case studies, OSHA/PSM incident narratives adapted to oilfield context) -- enough volume to support a meaningful train/test split. 

- Where genuinely public data is thin, generate additional synthetic narratives grounded in realistic OIL operational contexts (drilling, workover, pipeline, flow-station), explicitly labelled as synthetic and disclosed as such in the demo -- a team that is upfront about this is more credible than one that quietly blends synthetic and real data. 

- Independently label a sample using the energy+control framework (Section 5.1) to produce ground truth, and report inter-labeller agreement -- this single step visibly demonstrates methodological rigor to a judging panel. 

### **11.2 Metrics** 

|**Metric**|**Defniton**|**Prototype target**|
|---|---|---|
|SIF classifcaton recall|% of true SIF-potental reports (per<br>expert labels) correctly fagged by the<br>model|>= 0.85 (bias toward catching<br>over missing -- a missed SIF<br>precursor is the costlier error)|
|SIF classifcaton precision|% of model-fagged SIF-potental<br>reports that are true positves|>= 0.70|
|Life-Saving Rule top-1 accuracy|% of SIF-potental reports where the<br>top-ranked predicted rule matches the<br>expert label|>= 0.75|
|Life-Saving Rule top-2 accuracy|% where the correct rule is in the<br>model's top-2 ranked predictons|>= 0.90|
|Discrepancy catch rate|Number of test reports where the fler<br>under-classifed severity but the<br>model correctly fagged SIF potental|Reported as a concrete demo<br>highlight -- the clearest<br>before/afer story|
|Baseline comparison|Model performance vs. a simple<br>keyword-matching baseline (e.g. fag<br>on words like 'fall', 'struck', 'burn')|Report the delta explicitly -- this is<br>what proves the energy+control<br>approach adds value over naive<br>text search|



### **11.3 What to show live on stage** 

A short, rehearsed sequence: feed in 3-4 real-sounding report narratives live (including at least one where the filer's own severity tag is wrong), show the model's classification, evidence, and Life-Saving Rule tag appear on the dashboard in seconds, then show the density-ranking view update. This sequence directly demonstrates all three asks (a), (b), and (c) from the problem statement in one flow. 

Page 12 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **12. Data Requirements & Handling** 

### **12.1 Required data fields** 

- Report ID, timestamp, report type (UA / UC / near-miss / incident) 

- Free-text narrative (the primary NLP input) 

- Site / location identifier 

- Activity or work-type, if separately captured 

- Filer-selected severity/category (used as a comparison baseline, not ground truth) 

- (For training/validation only) expert-assigned SIF label and Life-Saving Rule tag, on a sample of reports -- see Section 11.1 

### **12.2 Data sensitivity & governance** 

- Field reports may contain personal details (names, employee IDs) -- the prototype should demonstrate PII redaction/masking in the preprocessing stage before text reaches any model, especially any external API. 

- The prototype defaults to open-source/self-hostable models for anything touching realistic operational data; an external LLM API is treated as an optional, explicitly-flagged configuration choice, not a default, given the sensitivity of safety-incident text. 

- Role-scoped dashboard access (a site HSE manager sees their site in depth; corporate HSSE sees all sites) is noted as a requirement even if simplified for the demo. 

Page 13 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **13. Non-Functional Requirements** 

|**Category**|**Requirement**|
|---|---|
|Performance|Single-report classifcaton latency < 3 seconds; batch throughput sufcient to process a<br>demo-scale dataset (hundreds to low thousands of records) within seconds to a few<br>minutes.|
|Explainability|Every classifcaton must expose the evidence (matched energy-source cue, control-failure<br>cue, Life-Saving Rule keyword span) -- non-negotable for HSE trust and regulatory<br>defensibility.|
|Reliability|Ingeston failures must degrade gracefully (quarantne, not silent drop).|
|Auditability|Full history of model version, confdence score, and any human override retained per<br>report.|
|Security|PII redacton before any external processing; role-based access control on the dashboard;<br>encrypted storage and transit for all report data.|
|Scalability|Architecture should scale from a single-feld pilot to a full mult-asset rollout without<br>redesign -- horizontal scaling of the NLP service layer.|
|Usability|Dashboard usable by HSE professionals without data-science background; no requirement<br>to understand model internals to act on its output.|
|Language robustness|Must not silently fail or misclassify on code-mixed (English/Hindi/Assamese-in-Latn-script)<br>or abbreviaton-heavy feld narratves.|
|Portability|No component may assume the internals or API surface of any specifc external HSSE<br>platorm -- the only external contract is the ingeston schema in Secton 4.1.|



## **14. Relationship to OIL's Existing HSSE Platform** 

OIL's HSSE reports are currently captured and stored through its existing HSSE reporting workflow. This PRD deliberately does not build the prototype's core value proposition around integration with, or assumptions about, that platform's internal architecture. 

A classification/analytics engine that depends on zero platform-specific integration can be pointed at any current or future data source OIL uses. This is a strength of the design, not a gap: OIL is not locked into a particular vendor relationship for this capability to work. 

##### **What this means in practice** 

The product's only interface to the outside world is the ingestion schema defined in Section 4.1 (report ID, timestamp, site, activity, free-text narrative). Any existing or future HSSE system connects by exporting or streaming data in that shape -- whether via a scheduled file export, a database view, or a live API, whichever OIL's IT and platform teams determine is feasible post-hackathon. That integration mechanics decision is explicitly out of scope for this prototype and is not required to prove the product works. 

Page 14 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **15. Risks & Mitigations** 

|**#**|**Risk**|**Mitgaton**|
|---|---|---|
|R1|No access to real OIL report data during the<br>hackathon, limitng model realism.|Use public oil & gas incident-report corpora plus<br>clearly-disclosed synthetc narratves (Secton 11.1); be<br>transparent about this in the demo rather than<br>implying the data is real.|
|R2|False negatves (missing a real SIF precursor)<br>carry outsized safety cost compared to false<br>positves.|Bias the classifcaton threshold toward recall; route<br>low-confdence cases to a human-review queue rather<br>than auto-clearing them (FR-3.3).|
|R3|Reviewers distrust an AI classifcaton they can't<br>interrogate.|Mandatory evidence/ratonale display on every output<br>(FR-4.2, FR-5.3); human-override is frst-class, not<br>bolted on.|
|R4|Code-mixed/regional-language narratves<br>degrade model accuracy.|Explicit design requirement (FR-2.2, NFR language<br>robustness) rather than an assumpton of clean English<br>text; validate on code-mixed samples specifcally.|
|R5|Over-ftng the Life-Saving Rule taxonomy to<br>hackathon example phrasing, failing to<br>generalise.|Keep the taxonomy-seed table (Secton 6) as training<br>signal, not a hard keyword-match rule; core<br>classifcaton relies on embeddings + energy/control<br>detecton, which generalise beter than literal phrase<br>matching.|
|R6|Judges probe on 'how would this connect to<br>our real system' and the team has no good<br>answer.|Secton 14 gives the team a clear, honest answer: a<br>documented, source-agnostc ingeston contract -- a<br>stronger positon than an unverifable integraton<br>claim.|



## **16. Future Roadmap (Post-Hackathon)** 

- Live connection to OIL's chosen HSSE data source, via whichever export/API mechanism OIL's IT team determines is feasible -- scoped as a discovery conversation once the prototype's value is validated. 

- Predictive layer: move from descriptive precursor density to a leading-indicator risk score per site/activity, validated against actual incident outcomes over time. 

- Automated retraining pipeline with scheduled model refresh from the growing labelled-examples store. 

- Optional guided-filing prompts at the point of report submission (e.g. 'was a permit in place?') that improve narrative completeness without adding friction, feeding cleaner data into the classifier. 

- Mobile-first guided filing assistant: optional, non-mandatory prompts at the point of filing (e.g. 'was a permit in place?') that improve narrative completeness without adding friction, feeding cleaner data into the classifier. 

- Benchmarking dashboard against DEKRA/EEI industry SIF-exposure-rate baselines (e.g. the ~25% crossindustry SIF rate cited in the problem statement) so OIL can see how its own precursor rate compares to peers. 

Page 15 of 16 

PRD · SIF-Precursor AI/NLP Engine for OIL HSSE 

## **17. Appendix: Reference Frameworks** 

### **17.1 IOGP Life-Saving Rules (10 rules)** 

- Bypassing Safety Controls 

- Confined Space 

- Driving 

- Energy Isolation 

- Hot Work 

- Line of Fire 

- Safe Mechanical Lifting 

- Management of Change 

- Permit to Work 

- Working at Height 

### **17.2 Key external references informing this PRD** 

- Martin, D. & Black, A. (2015). Preventing Serious Injuries and Fatalities: A New Study Reveals Precursors and Paradigms. DEKRA Insight. 

- Edison Electric Institute (EEI). The Power to Prevent SIF -- Safety Classification and Learning (SCL) Model. 

- DEKRA (2018/2019). Serious Injury and Fatality (SIF) exposure-rate research across industry sectors. 

- IOGP Life-Saving Rules framework (International Association of Oil & Gas Producers). 

- VelocityEHS (2024) PSIF classifier -- referenced in the problem statement as an existing industry approach to potential-SIF text classification. 

### **17.3 Glossary** 

|**Term**|**Meaning**|
|---|---|
|SIF|Serious Injury or Fatality -- an actual life-threatening, life-altering, or fatal workplace<br>event.|
|SIF precursor / PSIF|A high-risk situaton (high energy + absent/inefectve/non-complied control) with the<br>potental to cause a SIF, regardless of actual outcome severity.|
|UA / UC|Unsafe Act / Unsafe Conditon -- proactve safety observatons logged before any<br>incident occurs.|
|Direct control|A specifc barrier (isolaton, guarding, PPE, permit, procedure) intended to manage a<br>high-energy source during a task.|
|Life-Saving Rule|One of IOGP's 10 industry-standard rules addressing the actvites most associated with<br>fatalites in oil & gas operatons.|



Page 16 of 16 

