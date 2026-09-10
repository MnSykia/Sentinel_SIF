# SentinelSIF

SentinelSIF turns free-text HSSE observations into explainable SIF precursor intelligence. The dashboard starts empty: reports are added through CSV/JSON ingestion or the Live Report form and persist in SQLite.

## Start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. Copy `.env.example` to `.env` or set environment variables before starting if a non-default database location/origin is required. `SENTINELSIF_DATABASE_URL` defaults to `data/sentinelsif.db`; `SENTINELSIF_CORS_ORIGINS` defaults to local port 8000.

## API

- `POST /api/reports/upload` — multipart CSV/JSON upload; returns imported, duplicates, and validation failures.
- `POST /api/reports` — submit one live report.
- `GET /api/reports`, `GET /api/reports/{report_id}` — explorer data and report detail.
- `POST /api/reports/{report_id}/override` — persist a reviewer decision.
- `GET /api/dashboard/summary`, `/density`, `/life-saving-rules`, `/barrier-failures`, `/trends` — dashboard aggregates.

CSV/JSON accepts canonical fields `report_id`, `timestamp`, `report_type`, `site`, `activity`, `narrative`, `filer_selected_severity`; common aliases are normalized at the API boundary. The ML embedding head is optional at runtime: if its local model cannot be loaded, the existing explainable energy/control/LSR pipeline still runs.
