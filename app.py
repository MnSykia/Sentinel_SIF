"""SentinelSIF API: persistent report ingestion, analysis and review."""
import csv, io, json, logging, os, sqlite3, uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sentinelsif.classifier import SentinelClassifier

ROOT = Path(__file__).parent
DB_PATH = Path(os.getenv("SENTINELSIF_DATABASE_URL", str(ROOT / "data" / "sentinelsif.db")))
DEMO_DATASET_PATH = ROOT / "data" / "dataset.json"
ALIASES = {"report_id": ("report_id","id"), "timestamp": ("timestamp","date"), "site": ("site","location"), "activity": ("activity","work_type"), "narrative": ("narrative","description","free_text"), "filer_severity": ("filer_selected_severity","filer_severity","severity","category"), "report_type": ("report_type","type")}
engine = SentinelClassifier()
logger = logging.getLogger("sentinelsif.upload")
app = FastAPI(title="SentinelSIF API", version="3.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("SENTINELSIF_CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "templates")

@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True); con = sqlite3.connect(DB_PATH); con.row_factory = sqlite3.Row
    try: yield con; con.commit()
    finally: con.close()

@app.on_event("startup")
def startup():
    with db() as con: con.executescript("""CREATE TABLE IF NOT EXISTS reports(report_id TEXT PRIMARY KEY,timestamp TEXT NOT NULL,report_type TEXT NOT NULL,site TEXT NOT NULL,activity TEXT NOT NULL,narrative TEXT NOT NULL,filer_severity TEXT,source TEXT NOT NULL,model_output TEXT NOT NULL,created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS overrides(id INTEGER PRIMARY KEY,report_id TEXT NOT NULL,original_sif INTEGER NOT NULL,original_confidence REAL NOT NULL,overridden_sif INTEGER NOT NULL,reviewer TEXT NOT NULL,reason TEXT,created_at TEXT NOT NULL);""")
    # Model-development examples train the classifier only; they are never ingested as dashboard reports.
    engine.train_on_data(str(ROOT / "data" / "train_split.json"))

class ReportSubmission(BaseModel):
    report_id: Optional[str] = None; timestamp: Optional[datetime] = None; report_type: str = "Observation"
    site: str = Field(min_length=1); activity: str = Field(min_length=1); narrative: str = Field(min_length=5)
    filer_selected_severity: Optional[str] = None
class OverrideSubmission(BaseModel):
    classification: bool; reviewer: str = Field(min_length=2, max_length=100); reason: Optional[str] = Field(None, max_length=1000)

def normalise(raw: dict[str, Any], source: str):
    x = {str(k).strip().lower(): v for k,v in raw.items()}; get = lambda n: next((x[k] for k in ALIASES[n] if x.get(k) not in (None,"")), None)
    errors=[]; rid=get("report_id"); narrative=get("narrative"); site=get("site"); activity=get("activity"); ts=get("timestamp") or datetime.now(timezone.utc).isoformat()
    if not rid: errors.append("missing report_id (or id)")
    if not isinstance(narrative,str) or len(narrative.strip())<5: errors.append("narrative must be text with at least 5 characters")
    if not site: errors.append("missing site/location")
    if not activity: errors.append("missing activity/work_type")
    try: datetime.fromisoformat(str(ts).replace("Z","+00:00"))
    except ValueError: errors.append("timestamp/date must be ISO-8601 compatible")
    if errors: return None,errors
    return {"report_id":str(rid).strip(),"timestamp":str(ts),"report_type":str(get("report_type") or "Observation"),"site":str(site).strip(),"activity":str(activity).strip(),"narrative":narrative.strip(),"filer_severity":str(get("filer_severity") or "Unspecified"),"source":source},[]

def report_from_row(row):
    r=json.loads(row["model_output"]); r.update({k:row[k] for k in ("report_id","timestamp","report_type","site","activity","narrative","filer_severity","source")})
    with db() as con: history=[dict(x) for x in con.execute("SELECT overridden_sif,reviewer,reason,created_at FROM overrides WHERE report_id=? ORDER BY id",(row["report_id"],))]
    review_reasons=[]
    if r.get("needs_review"): review_reasons.append("Low confidence")
    if r.get("is_discrepancy"): review_reasons.append("Filer/model discrepancy")
    r["review_reasons"]=review_reasons
    r["override_history"]=history
    if history:
        # The reviewer decision is effective immediately; retain model output and
        # history for audit while removing an already-reviewed item from the queue.
        r.update(model_sif_potential=r["sif_potential"],sif_potential=bool(history[-1]["overridden_sif"]),human_override=True,reviewer_decision="SIF Potential" if history[-1]["overridden_sif"] else "Non-SIF",needs_review=False,is_discrepancy=False,review_reasons=[])
    return r
def all_reports():
    with db() as con: rows=con.execute("SELECT * FROM reports ORDER BY timestamp DESC").fetchall()
    return [report_from_row(x) for x in rows]
def persist(record):
    result=engine.analyze_report(record)
    with db() as con: con.execute("INSERT INTO reports VALUES (?,?,?,?,?,?,?,?,?,?)",(*[record[k] for k in ("report_id","timestamp","report_type","site","activity","narrative","filer_severity","source")],json.dumps(result),datetime.now(timezone.utc).isoformat()))
    return result

@app.get("/",response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )
@app.get("/api/reports")
def reports(site:Optional[str]=None,sif_only:bool=False,review_only:bool=False):
    r=all_reports(); return [x for x in r if (not site or x["site"]==site) and (not sif_only or x["sif_potential"]) and (not review_only or x["needs_review"] or x["is_discrepancy"])]
@app.get("/api/reports/{report_id}")
def report(report_id:str):
    with db() as con: row=con.execute("SELECT * FROM reports WHERE report_id=?",(report_id,)).fetchone()
    if not row: raise HTTPException(404,"Report not found")
    return report_from_row(row)
@app.post("/api/reports",status_code=201)
def create(sub:ReportSubmission):
    raw=sub.model_dump(); raw["report_id"]=sub.report_id or f"LIVE-{uuid.uuid4().hex[:10].upper()}"; raw["timestamp"]=sub.timestamp.isoformat() if sub.timestamp else datetime.now(timezone.utc).isoformat(); rec,errs=normalise(raw,"live")
    if errs: raise HTTPException(422,{"message":"Report validation failed","errors":errs})
    try: return persist(rec)
    except sqlite3.IntegrityError: raise HTTPException(409,"A report with this report_id already exists")
@app.post("/api/reports/upload")
async def upload(file:UploadFile=File(...)):
    name=(file.filename or "").lower()
    logger.info("Upload received: filename=%r content_type=%r", file.filename, file.content_type)
    if not name.endswith((".csv",".json")):
        logger.warning("Upload rejected: unsupported filename=%r", file.filename)
        raise HTTPException(415,"Invalid file type. Upload a CSV or JSON file.")
    try:
        content=(await file.read()).decode("utf-8-sig")
        if not content.strip(): raise ValueError("The uploaded file is empty")
        if name.endswith(".csv"):
            reader=csv.DictReader(io.StringIO(content))
            if not reader.fieldnames or any(not header or not header.strip() for header in reader.fieldnames): raise ValueError("CSV must include a valid header row")
            headers={header.strip().lower() for header in reader.fieldnames}
            missing=[field for field in ("report_id","site","activity","narrative") if not any(alias in headers for alias in ALIASES[field])]
            if missing: raise ValueError("Missing required CSV column(s): " + ", ".join(missing))
            items=list(reader)
        else: items=json.loads(content)
        if isinstance(items,dict): items=items.get("reports",[items])
        if not isinstance(items,list): raise ValueError("JSON must contain an array of report objects")
    except (UnicodeDecodeError, csv.Error, json.JSONDecodeError, ValueError) as e:
        logger.warning("Upload parse failure for %r: %s", file.filename, e)
        raise HTTPException(400,f"Invalid upload: {e}")
    logger.info("Upload parsed: filename=%r records=%d", file.filename, len(items))
    valid=[]; invalid=[]; seen=set(); duplicate_in_upload=[]
    for i,item in enumerate(items,1):
        rec,errs=normalise(item,"upload") if isinstance(item,dict) else (None,["record must be an object"])
        if rec and rec["report_id"] in seen:
            errs.append("duplicate report_id in this upload")
            duplicate_in_upload.append(rec["report_id"])
        if errs: invalid.append({"row":i,"report_id":rec["report_id"] if rec else None,"errors":errs})
        else: valid.append(rec); seen.add(rec["report_id"])
    with db() as con: existing={x[0] for x in con.execute("SELECT report_id FROM reports").fetchall()}
    accepted=[r for r in valid if r["report_id"] not in existing]; duplicates=duplicate_in_upload+[r["report_id"] for r in valid if r["report_id"] in existing]
    processing_errors=[]
    for rec in accepted:
        try: persist(rec)
        except Exception:
            # Log developer detail, but keep implementation details out of API/UI.
            logger.exception("Upload processing failed: report_id=%s", rec["report_id"])
            processing_errors.append({"row": None, "report_id": rec["report_id"], "errors": ["Backend processing error; this report was not imported"]})
    errors=invalid+processing_errors; imported_count=len(accepted)-len(processing_errors)
    logger.info("Upload complete: filename=%r imported=%d rejected=%d duplicates=%d", file.filename, imported_count, len(errors), len(duplicates))
    return {"total_records":len(items),"imported_count":imported_count,"rejected_count":len(errors),"duplicate_count":len(duplicates),"errors":errors,"imported":imported_count,"duplicates":duplicates,"invalid_records":errors,"message":"Import completed" if not errors else "Import completed with validation errors"}
@app.post("/api/reports/{report_id}/override")
def override(report_id:str,payload:OverrideSubmission):
    with db() as con:
        row=con.execute("SELECT model_output FROM reports WHERE report_id=?",(report_id,)).fetchone()
        if not row: raise HTTPException(404,"Report not found")
        model=json.loads(row[0]); con.execute("INSERT INTO overrides(report_id,original_sif,original_confidence,overridden_sif,reviewer,reason,created_at) VALUES(?,?,?,?,?,?,?)",(report_id,int(model["sif_potential"]),model["confidence_score"],int(payload.classification),payload.reviewer,payload.reason,datetime.now(timezone.utc).isoformat()))
    return report(report_id)

@app.delete("/api/reports/{report_id}")
def delete_report(report_id: str):
    """Delete a report and every persisted review decision associated with it."""
    with db() as con:
        exists=con.execute("SELECT 1 FROM reports WHERE report_id=?",(report_id,)).fetchone()
        if not exists: raise HTTPException(404,"Report not found")
        con.execute("DELETE FROM overrides WHERE report_id=?",(report_id,))
        con.execute("DELETE FROM reports WHERE report_id=?",(report_id,))
    logger.info("Deleted report and related reviews: %s", report_id)
    return {"message":"Report deleted", "report_id":report_id}

def clear_persisted_data(source: Optional[str] = None):
    with db() as con:
        if source:
            ids=[row[0] for row in con.execute("SELECT report_id FROM reports WHERE source=?",(source,))]
            if ids:
                placeholders=",".join("?" for _ in ids)
                con.execute(f"DELETE FROM overrides WHERE report_id IN ({placeholders})",ids)
                con.execute("DELETE FROM reports WHERE source=?",(source,))
            return len(ids)
        count=con.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
        con.execute("DELETE FROM overrides")
        con.execute("DELETE FROM reports")
        return count

@app.post("/api/data/clear-all")
def clear_all_data():
    removed=clear_persisted_data()
    logger.info("Cleared all persisted data: %d reports", removed)
    return {"message":"All SentinelSIF data was permanently removed", "removed_count":removed}

@app.post("/api/data/clear-uploaded")
def clear_uploaded_data():
    return {"message":"Uploaded reports removed", "removed_count":clear_persisted_data("upload")}

@app.post("/api/data/clear-live")
def clear_live_data():
    return {"message":"Live reports removed", "removed_count":clear_persisted_data("live")}

@app.post("/api/data/reset-demo")
def reset_demo_data():
    if not DEMO_DATASET_PATH.exists(): raise HTTPException(500,"The bundled demonstration dataset is unavailable")
    try:
        records=json.loads(DEMO_DATASET_PATH.read_text(encoding="utf-8"))
        if not isinstance(records,list): raise ValueError("Demo dataset is not a list")
    except (OSError, json.JSONDecodeError, ValueError):
        logger.exception("Unable to read bundled demo dataset")
        raise HTTPException(500,"The bundled demonstration dataset could not be loaded")
    clear_persisted_data()
    rejected=[]; imported=0
    for index, raw in enumerate(records,1):
        record, errors=normalise(raw,"demo")
        if errors: rejected.append({"row":index,"errors":errors}); continue
        try: persist(record); imported+=1
        except Exception:
            logger.exception("Demo record processing failed at row %s", index)
            rejected.append({"row":index,"errors":["Demo record processing failed"]})
    return {"message":"Demo dataset reset", "imported_count":imported, "rejected_count":len(rejected), "errors":rejected}

def report_day(timestamp: str) -> date:
    return datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).date()

def trend_series(data, date_from: Optional[str] = None, date_to: Optional[str] = None):
    days=[report_day(r["timestamp"]) for r in data]
    start=date.fromisoformat(date_from) if date_from else (min(days) if days else None)
    end=date.fromisoformat(date_to) if date_to else (max(days) if days else None)
    if not start or not end or start > end: return {"aggregation":"weekly","points":[]}
    monthly=(end-start).days > 90
    bucket_start=lambda day: day.replace(day=1) if monthly else day-timedelta(days=day.weekday())
    current=bucket_start(start); last=bucket_start(end); buckets=[]
    while current <= last:
        buckets.append(current)
        current=(current.replace(day=28)+timedelta(days=4)).replace(day=1) if monthly else current+timedelta(days=7)
    counts={bucket:{"total_reports":0,"sif_count":0} for bucket in buckets}
    for report, day in zip(data, days):
        bucket=bucket_start(day)
        if bucket in counts:
            counts[bucket]["total_reports"]+=1
            counts[bucket]["sif_count"]+=int(report["sif_potential"])
    return {"aggregation":"monthly" if monthly else "weekly","points":[{"period":bucket.isoformat(),"label":bucket.strftime("%Y-%m" if monthly else "%d %b"),"total_reports":values["total_reports"],"sif_count":values["sif_count"],"rate":round(100*values["sif_count"]/values["total_reports"],1) if values["total_reports"] else 0} for bucket, values in counts.items()]}

def summary(date_from: Optional[str] = None, date_to: Optional[str] = None, site: Optional[str] = None, activity: Optional[str] = None, life_saving_rule: Optional[str] = None):
    data=all_reports()
    if date_from: data=[r for r in data if r["timestamp"][:10] >= date_from]
    if date_to: data=[r for r in data if r["timestamp"][:10] <= date_to]
    if site: data=[r for r in data if r["site"] == site]
    if activity: data=[r for r in data if r["activity"] == activity]
    if life_saving_rule: data=[r for r in data if any(x["rule"] == life_saving_rule for x in r["life_saving_rules"])]
    flagged=[r for r in data if r["sif_potential"]]
    def ranked(key):
        out=[]
        for value in sorted({r[key] for r in data}):
            group=[r for r in data if r[key]==value]; count=sum(r["sif_potential"] for r in group); out.append({key:value,"total_reports":len(group),"sif_count":count,"sif_density":round(100*count/len(group),1)})
        return sorted(out,key=lambda x:x["sif_density"],reverse=True)
    def priority_candidates(key):
        candidates=[]
        for value in sorted({r[key] for r in data}):
            group=[r for r in data if r[key]==value]; flagged_group=[r for r in group if r["sif_potential"]]
            if not flagged_group: continue
            signals=[]
            for report in flagged_group:
                signals.extend(x["rule"] for x in report["life_saving_rules"] if x.get("rule") != "None")
                if report["barrier_failure_category"] != "None": signals.append(report["barrier_failure_category"])
            dominant=max(set(signals),key=lambda signal:(signals.count(signal),signal)) if signals else "No specific signal"
            candidates.append({"dimension":key,"label":value,"sif_count":len(flagged_group),"total_reports":len(group),"density":round(100*len(flagged_group)/len(group),1),"dominant_signal":dominant})
        return candidates
    lsr={}; barriers={}; energy={}; energy_none_count=0
    for r in data:
        source=r.get("energy_source") or "None"
        if source == "None": energy_none_count+=1
        else: energy[source]=energy.get(source,0)+1
    for r in flagged:
        for tag in r["life_saving_rules"]: lsr[tag["rule"]]=lsr.get(tag["rule"],0)+1
        if r["barrier_failure_category"]!="None": barriers[r["barrier_failure_category"]]=barriers.get(r["barrier_failure_category"],0)+1
    precursor_total=sum(barriers.values())
    precursor_signals=[{"signal":name,"count":count,"share":round(100*count/precursor_total,1) if precursor_total else 0} for name,count in sorted(barriers.items(),key=lambda item:(-item[1],item[0]))]
    matrix_counts={}
    for report in flagged:
        category=report["barrier_failure_category"]
        if category != "None":
            matrix_counts.setdefault(report["activity"],{})[category]=matrix_counts.setdefault(report["activity"],{}).get(category,0)+1
    matrix_categories=sorted({category for counts in matrix_counts.values() for category in counts},key=lambda category:(-sum(counts.get(category,0) for counts in matrix_counts.values()),category))
    activity_barrier_matrix={"categories":matrix_categories,"rows":[{"activity":activity,"counts":counts,"total":sum(counts.values())} for activity,counts in sorted(matrix_counts.items(),key=lambda item:(-sum(item[1].values()),item[0]))]}
    priority_attention=sorted(priority_candidates("site")+priority_candidates("activity"),key=lambda item:(-item["density"],-item["sif_count"],-item["total_reports"],item["label"]))[:3]
    return {"total_reports":len(data),"sif_count":len(flagged),"sif_density_overall":round(100*len(flagged)/len(data),1) if data else 0,"discrepancy_count":sum(r["is_discrepancy"] for r in data),"review_count":sum(r["needs_review"] or r["is_discrepancy"] for r in data),"site_rankings":ranked("site"),"activity_rankings":ranked("activity"),"lsr_distribution":lsr,"barrier_distribution":barriers,"energy_distribution":energy,"energy_none_count":energy_none_count,"precursor_signals":precursor_signals,"activity_barrier_matrix":activity_barrier_matrix,"priority_attention":priority_attention,"sif_precursor_trend":trend_series(data,date_from,date_to)}
@app.get("/api/dashboard/summary")
def dashboard_summary(date_from: Optional[str] = None, date_to: Optional[str] = None, site: Optional[str] = None, activity: Optional[str] = None, life_saving_rule: Optional[str] = None):
    return summary(date_from, date_to, site, activity, life_saving_rule)
@app.get("/api/dashboard/density")
def density(): s=summary(); return {"sites":s["site_rankings"],"activities":s["activity_rankings"]}
@app.get("/api/dashboard/life-saving-rules")
def lsr(): return summary()["lsr_distribution"]
@app.get("/api/dashboard/barrier-failures")
def barriers(): return summary()["barrier_distribution"]
@app.get("/api/dashboard/trends")
def trends(date_from: Optional[str] = None, date_to: Optional[str] = None, site: Optional[str] = None, activity: Optional[str] = None, life_saving_rule: Optional[str] = None):
    return summary(date_from, date_to, site, activity, life_saving_rule)["sif_precursor_trend"]
