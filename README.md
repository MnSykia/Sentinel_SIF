````markdown
# SentinelSIF

### AI/NLP Engine for Detecting Serious Injury & Fatality (SIF) Precursors in HSSE Reports

SentinelSIF is an explainable AI/NLP engine designed for Oil India Limited (OIL) to identify **Serious Injury & Fatality (SIF) precursors** hidden within Unsafe Act (UA), Unsafe Condition (UC), near-miss, and incident reports.

Instead of relying on reported injury severity, SentinelSIF evaluates the combination of:

> **High-energy exposure + failed, absent, or ineffective direct control**

This allows HSE teams to identify reports with potentially life-threatening consequences, prioritize review, and discover recurring precursor patterns across sites and activities.

The prototype is developed for **Smart India Hackathon (SIH) 2026** by Team Sentinels.

---

## Problem

OIL's HSSE workflow generates large volumes of structured reports containing free-text narratives. Traditionally, these narratives are reviewed manually at periodic intervals. This creates a visibility gap: a report classified as "Low" or "Medium" severity can still describe a situation with the potential to cause a fatality or life-altering injury. SentinelSIF addresses this gap by automatically analyzing each report and surfacing the reports and patterns that deserve immediate HSE attention.

The system focuses on three outcomes:

1. **SIF-Potential Classification**
   - Classifies reports as SIF-potential or Non-SIF-potential.
   - Prioritizes high recall because missed SIF precursors carry greater safety cost.

2. **Life-Saving Rule Tagging**
   - Maps SIF-potential reports to the relevant IOGP Life-Saving Rule(s).

3. **Precursor Pattern Intelligence**
   - Identifies recurring patterns across:
     - Sites / locations
     - Activities
     - Energy sources
     - Barrier/control failures
     - Life-Saving Rules

The dashboard ranks sites and activities by **SIF-precursor density**, rather than raw report volume, helping HSE teams focus attention where fatal-potential exposure is concentrated.

---

## Key Concept

A SIF precursor is not defined by the severity of the outcome. SentinelSIF looks for a high-energy situation in which the direct control intended to manage that energy is absent, ineffective, or not followed.

Examples of high-energy exposure include:

- Electrical energy
- Stored or pressurized energy
- Mechanical energy
- Gravity / elevation
- Vehicle kinetic energy
- Chemical / thermal energy
- Hydrocarbon-related energy

Examples of direct controls include:

- Energy isolation / LOTO
- Guarding
- Permit to Work
- Gas testing
- Fall protection
- Exclusion zones
- Lifting plans
- Required PPE
- Safe operating procedures

This **energy + control** approach is the core classification logic of SentinelSIF. It deliberately avoids treating filer-selected severity as ground truth. :contentReference[oaicite:1]{index=1}

---

## Features

### AI/NLP Classification

Analyzes free-text HSSE narratives and identifies SIF-potential reports using a hybrid approach combining:

- Sentence-Transformer semantic embeddings
- Logistic Regression classification
- Energy-source detection
- Direct-control detection
- Rule/taxonomy logic

The architecture is designed to provide semantic understanding while retaining interpretable safety logic.

### Explainable AI

Every classification can expose:

- Detected energy source
- Control/barrier status
- Evidence spans
- Life-Saving Rule
- Precursor category
- Decision rationale
- Confidence score

The objective is not simply to produce a prediction, but to show an HSE reviewer **why the report was flagged**.

### IOGP Life-Saving Rules

SentinelSIF supports tagging against the 10 IOGP Life-Saving Rules:

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

### Precursor Pattern Detection

The system extracts and aggregates recurring patterns across:

- Site
- Activity
- Energy source
- Barrier-failure category
- Life-Saving Rule

### Risk-Concentration Dashboard

The dashboard provides:

- SIF-precursor density rankings
- Site risk concentration
- Activity rankings
- Life-Saving Rule distribution
- Barrier-failure patterns
- Trends over time
- Report-level drill-down
- Discrepancy detection
- Human-review queue

Sites and activities are ranked using SIF-precursor density alongside absolute report counts to avoid allowing high-volume locations to dominate the analysis purely because they submit more reports.

### Human-in-the-Loop Review

Low-confidence cases and model/filer discrepancies can be reviewed by an HSE user.

Reviewers can:

- Inspect the original narrative
- Examine model evidence
- Accept or override the classification
- Add reviewer notes
- Preserve override history

Reviewer corrections can become labelled examples for future model refinement.

### Source-Agnostic Ingestion

SentinelSIF does not depend on the internal architecture of a specific HSSE platform.

Reports can be supplied through:

- CSV
- JSON
- REST API
- Live Report form

A documented ingestion schema allows an existing or future HSSE platform to map its exported data into SentinelSIF without requiring platform-specific assumptions.

---

## System Architecture

```text
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚   Report Sources     â”‚
                         â”‚ CSV / JSON / API     â”‚
                         â”‚ Live Report          â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                                    â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚ Ingestion &          â”‚
                         â”‚ Validation           â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                                    â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚ Text Preprocessing   â”‚
                         â”‚ Normalisation        â”‚
                         â”‚ Code-mix handling    â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                    â–¼                               â–¼
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”             â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â”‚ Energy Detector  â”‚             â”‚ Control Detector â”‚
          â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜             â””â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                   â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                   â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚ SIF Decision Logic  â”‚
                         â”‚ Energy + Control    â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                       â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                       â–¼                         â–¼
                 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                 â”‚ Confident â”‚            â”‚ Human Review â”‚
                 â”‚ Result    â”‚            â”‚ / Override   â”‚
                 â””â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”˜            â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”˜
                       â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚ LSR Tagger +        â”‚
                         â”‚ Precursor Extractor â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                                    â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚ SQLite Enrichment   â”‚
                         â”‚ Store               â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                    â”‚
                                    â–¼
                         â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                         â”‚ Analytics Dashboard â”‚
                         â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
````

The prototype follows a source-agnostic ingestion architecture so that the intelligence layer can sit above OIL's existing or future HSSE data source.

---

## Technology Stack

| Layer           | Technology                                |
| --------------- | ----------------------------------------- |
| Frontend        | HTML5, CSS3, Vanilla JavaScript           |
| Backend         | Python, FastAPI                           |
| API Server      | Uvicorn                                   |
| NLP             | Sentence-Transformers                     |
| Embedding Model | `all-MiniLM-L6-v2`                        |
| ML Classifier   | scikit-learn Logistic Regression          |
| Safety Logic    | Custom rule + taxonomy engine             |
| Data Processing | Pandas, NumPy                             |
| Validation      | Pydantic / FastAPI                        |
| Database        | SQLite                                    |
| Architecture    | REST API                                  |
| Explainability  | Evidence spans + energy/control rationale |

The PRD specifies a lightweight REST ingestion service, Python NLP pipeline, relational prototype store such as SQLite/PostgreSQL, analytics aggregation, dashboard, and reviewer feedback loop.

---

## Project Structure

```text
SentinelSIF/
â”‚
â”œâ”€â”€ app.py
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .env.example
â”‚
â”œâ”€â”€ sentinelsif/
â”‚   â”œâ”€â”€ classifier.py
â”‚   â”œâ”€â”€ preprocessor.py
â”‚   â”œâ”€â”€ energy_detector.py
â”‚   â”œâ”€â”€ control_detector.py
â”‚   â”œâ”€â”€ lsr_tagger.py
â”‚   â””â”€â”€ precursor_extractor.py
â”‚
â”œâ”€â”€ templates/
â”‚   â””â”€â”€ index.html
â”‚
â”œâ”€â”€ static/
â”‚   â”œâ”€â”€ css/
â”‚   â””â”€â”€ js/
â”‚
â”œâ”€â”€ data/
â”‚   â””â”€â”€ ...
â”‚
â””â”€â”€ README.md
```

---

## Getting Started

### 1. Clone the repository

```powershell
git clone https://github.com/<YOUR-USERNAME>/SentinelSIF.git
cd SentinelSIF
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again.

### 4. Install dependencies

```powershell
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy:

```text
.env.example
```

to:

```text
.env
```

The application can run with its default local configuration.

Default database:

```text
data/sentinelsif.db
```

Default local origin:

```text
http://127.0.0.1:8000
```

### 6. Start the application

```powershell
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

---

## Data Ingestion

SentinelSIF accepts CSV and JSON reports using the following canonical fields:

```text
report_id
timestamp
report_type
site
activity
narrative
filer_selected_severity
```

Common field aliases are normalized at the API boundary.

Example:

```csv
report_id,timestamp,report_type,site,activity,narrative,filer_selected_severity
SIF-001,2026-09-10T09:30:00,UA,Duliajan Field,Wellhead Maintenance,"LOTO was not verified before opening the equipment and stored pressure remained in the line.",Low
```

The filer-selected severity is treated as a comparison signal, **not as expert ground truth**.

---

## API

### Report Management

```text
POST /api/reports/upload
```

Upload CSV/JSON reports.

Returns imported records, duplicates, and validation failures.

```text
POST /api/reports
```

Submit a single live report.

```text
GET /api/reports
```

Retrieve report explorer data.

```text
GET /api/reports/{report_id}
```

Retrieve detailed model output for a report.

```text
POST /api/reports/{report_id}/override
```

Persist a reviewer classification decision.

### Dashboard

```text
GET /api/dashboard/summary
GET /api/dashboard/density
GET /api/dashboard/life-saving-rules
GET /api/dashboard/barrier-failures
GET /api/dashboard/trends
```

These endpoints provide the data used by the dashboard's operational analytics.

### Model Evaluation

```text
GET /api/evaluation
```

Returns measured evaluation metrics when a valid held-out labelled test set is available.

The evaluation layer is designed to report:

* SIF classification recall
* SIF classification precision
* Life-Saving Rule top-1 accuracy
* Life-Saving Rule top-2 accuracy
* Test-set size
* Model version
* Evaluation timestamp
* PRD target comparison

**Confidence scores must not be interpreted as measured model accuracy.**

---

## Model Evaluation

The SIH prototype defines the following target metrics:

| Metric             | Prototype Target |
| ------------------ | ---------------: |
| SIF Recall         |            â‰¥ 85% |
| SIF Precision      |            â‰¥ 70% |
| LSR Top-1 Accuracy |            â‰¥ 75% |
| LSR Top-2 Accuracy |            â‰¥ 90% |

Evaluation must be performed against a genuinely held-out labelled test set and expert-reviewed ground truth. The targets reflect the PRD's emphasis on high recall because a missed SIF precursor carries greater safety cost than an additional false positive.

### Evaluation Data Provenance

No real OIL HSSE data was available to the development team for this prototype. The checked-in `data/dataset.json` contains synthetic development data generated by `data/dataset_generator.py`. It is not real OIL HSSE data, field validation data, or independently expert-reviewed data. Its `ground_truth` fields are generator metadata used for development benchmarking.

The current quantitative result is reported as a **Development Synthetic Benchmark**. It uses the 68 records in `data/dataset.json` whose stable `report_id` values are absent from `data/train_split.json`. These benchmark metrics demonstrate prototype behavior only and must not be presented as OIL validation, production accuracy, or expert-validated performance.

Formal evaluation is separate and reads `data/expert_reviewed_test.json`. That file is intentionally an empty template until an independently supplied dataset is available. Formal records must include `report_id`, `timestamp`, `report_type`, `site`, `activity`, `narrative`, boolean `ground_truth_sif`, list-valued `ground_truth_lsr`, `annotation_status: expert_reviewed`, positive `annotator_count`, `source_reference`, and `reviewed_at`. The evaluator rejects malformed records, duplicate IDs, invalid labels, and IDs overlapping the training split; it never silently removes leakage records.

Until that dataset is populated with genuinely independent expert review, the Model Performance page shows synthetic benchmark metrics separately and reports **Formal Expert Evaluation: Not Evaluated**.

### Operational Security and Storage

`SENTINELSIF_DATABASE_URL` is currently interpreted as a filesystem path to the SQLite database; it is not a SQLAlchemy-style connection URL. The prototype's report deletion, data-clearing, reset, and reviewer-override endpoints have no authentication or authorization layer. They are suitable for local/demo use only and must be protected by deployment-level authentication and authorization before production use.

---

## Explainability

For every analysed report, SentinelSIF attempts to expose the evidence behind the classification.

Example reasoning:

```text
SIF Potential: YES

Energy Source:
Electrical / Stored Pressure

Control Status:
Not Followed

Evidence:
"LOTO isolation was not verified"
"stored pressure remained in the line"

Primary Life-Saving Rule:
Energy Isolation

Barrier Failure:
Energy isolation not verified
```

This design supports HSE review rather than replacing it. Every AI-driven result is intended to remain traceable to the underlying report evidence.

---

## Human-in-the-Loop Workflow

```text
Report Submitted
       â”‚
       â–¼
AI/NLP Analysis
       â”‚
       â–¼
SIF Classification
       â”‚
       â”œâ”€â”€ High Confidence â”€â”€â–º Dashboard
       â”‚
       â””â”€â”€ Low Confidence / Discrepancy
                    â”‚
                    â–¼
              Human Review
                    â”‚
             â”Œâ”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”
             â–¼             â–¼
           Accept        Override
             â”‚             â”‚
             â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
                    â–¼
             Labelled Example
```

The reviewer override loop is a first-class component of the prototype and is intended to improve trust and provide corrected examples for future model refinement.

---

## SIH 2026 Prototype Scope

### In Scope

* Free-text UA/UC, near-miss, and incident ingestion
* SIF-potential binary classification
* IOGP Life-Saving Rule tagging
* Precursor pattern extraction
* Site and activity density ranking
* Dashboard analytics
* Report-level explainability
* Human review and override
* Generic ingestion contract
* Prototype model evaluation

### Out of Scope for the Hackathon Prototype

* Direct integration with OIL's production HSSE platform
* Fully automated MLOps/retraining pipeline
* Predictive forecasting of future fatality probability
* A dedicated mobile filing application

These capabilities are part of the post-hackathon roadmap rather than requirements of the current prototype.

---

## Security and Configuration

Do not commit secrets or local runtime data.

The following should remain outside version control:

```text
.venv/
.env
*.db
__pycache__/
.vscode/
```

Use `.env.example` to document required configuration without exposing credentials.

---

## SIH Demonstration Flow

The recommended demonstration sequence is:

```text
1. Submit / upload HSSE reports
          â†“
2. SentinelSIF analyses the narratives
          â†“
3. SIF-potential reports are identified
          â†“
4. Energy + control evidence is displayed
          â†“
5. Life-Saving Rules are assigned
          â†“
6. Precursor patterns are aggregated
          â†“
7. High-density sites / activities are ranked
          â†“
8. Reviewer opens a flagged report
          â†“
9. Reviewer accepts or overrides the result
          â†“
10. Correction is retained for future model refinement
```

This demonstrates the three core SIH requirements in one workflow: classification, Life-Saving Rule tagging, and recurring precursor-pattern discovery.

---

## Roadmap

Post-hackathon development can extend SentinelSIF with:

* Integration with OIL's selected HSSE data source
* Automated model retraining
* Leading-indicator risk scoring
* Guided report-filing prompts
* Mobile-first filing assistance
* Industry benchmarking against SIF exposure-rate baselines

These are future extensions and are not represented as capabilities of the current SIH prototype.

---

## Why SentinelSIF?

Traditional reporting tells an HSE team **what was reported**.

SentinelSIF is designed to answer three additional questions:

> **Which reports contain SIF potential?**

> **Which critical safety controls are failing?**

> **Where are these precursor patterns concentrating?**

The result is a shift from periodic manual review toward **near-real-time, evidence-backed SIF precursor intelligence**.

---

## Project Status

**Smart India Hackathon 2026 Prototype**

SentinelSIF is a hackathon prototype intended to demonstrate the feasibility of an explainable, source-agnostic SIF precursor intelligence layer for OIL's HSSE reporting ecosystem.

It is not a production safety system and should not be used as the sole basis for operational safety decisions.

```
