"""Provenance-aware, validation-first evaluation for SentinelSIF."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from sentinelsif.classifier import MODEL_VERSION, SentinelClassifier
from sentinelsif.lsr_tagger import LSR_TAXONOMY

PRD_TARGETS = {"sif_recall": 0.85, "sif_precision": 0.70, "lsr_top1": 0.75, "lsr_top2": 0.90}
REQUIRED_SYNTHETIC_GT = {"sif_potential", "life_saving_rules"}
REQUIRED_EXPERT_FIELDS = {"report_id", "timestamp", "report_type", "site", "activity", "narrative", "ground_truth_sif", "ground_truth_lsr"}
EXPERT_PROVENANCE_FIELDS = {"annotation_status", "annotator_count", "source_reference", "reviewed_at"}


def _read_records(path: Path) -> list[Any]:
    """Backward-compatible reader that preserves malformed list members for validation."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return payload if isinstance(payload, list) else []


def _read_records_detailed(path: Path) -> tuple[list[Any], str, list[str]]:
    if not path.exists():
        return [], "missing", [f"file not found: {path.as_posix()}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [], "invalid_json", [f"invalid JSON: {error}"]
    if not isinstance(payload, list):
        return [], "wrong_top_level", ["top-level JSON value must be an array"]
    return payload, "ok", []


def _valid_iso(value: Any, timezone_required: bool = False) -> bool:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return not timezone_required or (parsed.tzinfo is not None and parsed.utcoffset() is not None)


def _validate_lsr_list(value: Any, prefix: str, allow_empty: bool = True) -> list[str]:
    errors=[]
    if not isinstance(value, list):
        return [f"{prefix}: must be a list"]
    if not allow_empty and not value:
        errors.append(f"{prefix}: must contain at least one label")
    if all(isinstance(item, str) for item in value) and len(value) != len(set(value)):
        errors.append(f"{prefix}: duplicate labels are not allowed")
    for label in value:
        if not isinstance(label, str) or label not in LSR_TAXONOMY:
            errors.append(f"{prefix}: invalid Life-Saving Rule {label!r}")
    return errors


def _validate_synthetic_record(record: Any, prefix: str) -> list[str]:
    if not isinstance(record, dict):
        return [f"{prefix}: record must be an object"]
    errors=[]; report_id=record.get("report_id"); ground_truth=record.get("ground_truth")
    if not isinstance(report_id, str) or not report_id.strip(): errors.append(f"{prefix}: report_id must be a non-empty string")
    if not isinstance(record.get("narrative"), str) or not record["narrative"].strip(): errors.append(f"{prefix}: narrative must be non-empty text")
    if not isinstance(ground_truth, dict): return errors + [f"{prefix}: ground_truth must be an object"]
    missing=REQUIRED_SYNTHETIC_GT-set(ground_truth)
    errors.extend(f"{prefix}: ground_truth missing {field}" for field in sorted(missing))
    if "sif_potential" in ground_truth and not isinstance(ground_truth["sif_potential"], bool): errors.append(f"{prefix}: ground_truth.sif_potential must be boolean")
    if "life_saving_rules" in ground_truth: errors.extend(_validate_lsr_list(ground_truth["life_saving_rules"],f"{prefix}: ground_truth.life_saving_rules"))
    return errors


def _validate_synthetic_sets(master: list[Any], training: list[Any]) -> tuple[list[str], set[str], set[str]]:
    errors=[]; master_ids=[]; training_ids=[]
    for index, record in enumerate(master, 1):
        errors.extend(_validate_synthetic_record(record, f"dataset record {index}"))
        if isinstance(record, dict) and isinstance(record.get("report_id"), str): master_ids.append(record["report_id"])
    for index, record in enumerate(training, 1):
        errors.extend(_validate_synthetic_record(record, f"training record {index}"))
        if isinstance(record, dict) and isinstance(record.get("report_id"), str): training_ids.append(record["report_id"])
    for label, ids in (("dataset", master_ids), ("training", training_ids)):
        duplicates={item for item in ids if ids.count(item)>1}
        errors.extend(f"{label}: duplicate report_id {item}" for item in sorted(duplicates))
    master_set=set(master_ids); training_set=set(training_ids)
    errors.extend(f"training: report_id not present in dataset: {item}" for item in sorted(training_set-master_set))
    return errors, master_set, training_set


def load_held_out_records(root: Path) -> list[Any]:
    """Compatibility helper; callers needing validation should use evaluate_classifier."""
    master=_read_records(root / "data" / "dataset.json"); training=_read_records(root / "data" / "train_split.json")
    training_ids={item.get("report_id") for item in training if isinstance(item, dict) and item.get("report_id")}
    return [item for item in master if not isinstance(item, dict) or item.get("report_id") not in training_ids]


def validate_expert_records(records: list[Any], training_ids: set[str]) -> list[str]:
    errors=[]; seen=set()
    if not records: return ["expert_reviewed_test.json is empty"]
    for index, record in enumerate(records, 1):
        prefix=f"expert record {index}"
        if not isinstance(record, dict): errors.append(f"{prefix}: record must be an object"); continue
        missing=(REQUIRED_EXPERT_FIELDS|EXPERT_PROVENANCE_FIELDS)-set(record)
        errors.extend(f"{prefix}: missing field {field}" for field in sorted(missing))
        report_id=record.get("report_id")
        if not isinstance(report_id, str) or not report_id.strip(): errors.append(f"{prefix}: report_id must be a non-empty string")
        else:
            if report_id in seen: errors.append(f"{prefix}: duplicate report_id {report_id}")
            if report_id in training_ids: errors.append(f"{prefix}: report_id overlaps training data: {report_id}")
            seen.add(report_id)
        for field in ("timestamp", "reviewed_at"):
            if field in record and not _valid_iso(record[field], timezone_required=True): errors.append(f"{prefix}: {field} must be timezone-aware ISO-8601")
        for field in ("report_type", "site", "activity", "narrative"):
            if field in record and (not isinstance(record[field], str) or not record[field].strip()): errors.append(f"{prefix}: {field} must be non-empty text")
        if "ground_truth_sif" in record and not isinstance(record["ground_truth_sif"], bool): errors.append(f"{prefix}: ground_truth_sif must be boolean")
        if "ground_truth_lsr" in record: errors.extend(_validate_lsr_list(record["ground_truth_lsr"],f"{prefix}: ground_truth_lsr"))
        if record.get("annotation_status") != "expert_reviewed": errors.append(f"{prefix}: annotation_status must be expert_reviewed")
        count=record.get("annotator_count")
        if not isinstance(count, int) or isinstance(count, bool) or count < 1: errors.append(f"{prefix}: annotator_count must be an integer >= 1 and not boolean")
        if "source_reference" in record and (not isinstance(record["source_reference"], str) or not record["source_reference"].strip()): errors.append(f"{prefix}: source_reference is required")
    return errors


def _with_targets(metrics: dict[str, Any]) -> dict[str, Any]:
    measured={key:metrics.get(key) for key in PRD_TARGETS}
    return {"metrics":measured,"measured":measured.copy(),"targets":PRD_TARGETS.copy(),"pass_status":{key:value is not None and value>=PRD_TARGETS[key] for key,value in measured.items()}}


def _unavailable(status: str, message: str, validation: Optional[dict[str, Any]], evaluation_time: str) -> Dict[str, Any]:
    empty={key:None for key in PRD_TARGETS}
    return {"status":status,"evaluation_type":"none","message":message,"dataset_size":None,"test_set_size":None,"evaluation_dataset":None,"metrics":empty,"measured":empty.copy(),"targets":PRD_TARGETS.copy(),"pass_status":{key:None for key in PRD_TARGETS},"model_version":MODEL_VERSION,"evaluated_at":evaluation_time,"evaluation_timestamp":evaluation_time,"validation":validation or {"valid":False,"errors":[message]},"provenance":None}


def _metrics(records: list[dict[str, Any]], engine: SentinelClassifier, formal: bool = False) -> dict[str, Any]:
    true_sif=[]; predicted_sif=[]; top1=top2=lsr_cases=0
    for record in records:
        result=engine.analyze_report(record)
        if formal: truth_sif=record["ground_truth_sif"]; expected=set(record["ground_truth_lsr"])
        else: truth=record["ground_truth"]; truth_sif=bool(truth["sif_potential"]); expected=set(truth["life_saving_rules"])
        true_sif.append(truth_sif); predicted_sif.append(bool(result.get("sif_potential")))
        if truth_sif and expected:
            lsr_cases+=1
            # LSRTagger.tag sorts output by confidence descending; this is the ranking contract used here.
            predicted=[item["rule"] for item in result.get("life_saving_rules", [])]
            top1+=int(bool(predicted) and predicted[0] in expected); top2+=int(bool(set(predicted[:2]) & expected))
    tp=sum(actual and predicted for actual,predicted in zip(true_sif,predicted_sif)); actual=sum(true_sif); predicted=sum(predicted_sif)
    return {"sif_recall":tp/actual if actual else None,"sif_precision":tp/predicted if predicted else None,"lsr_top1":top1/lsr_cases if lsr_cases else None,"lsr_top2":top2/lsr_cases if lsr_cases else None,"lsr_evaluable_cases":lsr_cases}


def evaluate_classifier(root: Path, classifier: Optional[SentinelClassifier] = None, train_if_needed: Optional[bool] = None) -> Dict[str, Any]:
    """Evaluate without mutating datasets.

    When no classifier is supplied, a new classifier is trained on the fixed
    training split. A supplied classifier is never retrained by default;
    pass ``train_if_needed=True`` explicitly when that is intended.
    """
    evaluation_time=datetime.now(timezone.utc).isoformat()
    master, master_status, master_errors=_read_records_detailed(root/"data"/"dataset.json")
    training, training_status, training_errors=_read_records_detailed(root/"data"/"train_split.json")
    synthetic_errors=master_errors+training_errors
    master_ids=set(); training_ids=set()
    if master_status=="ok" and training_status=="ok":
        validation_errors, master_ids, training_ids=_validate_synthetic_sets(master,training); synthetic_errors.extend(validation_errors)
    synthetic=[record for record in master if isinstance(record,dict) and record.get("report_id") not in training_ids] if not synthetic_errors else []
    formal_records, formal_status, formal_read_errors=_read_records_detailed(root/"data"/"expert_reviewed_test.json")
    if classifier is None:
        engine=SentinelClassifier(); engine.train_on_data(str(root/"data"/"train_split.json"))
    else:
        engine=classifier
        if train_if_needed is True: engine.train_on_data(str(root/"data"/"train_split.json"))
        elif train_if_needed is None and getattr(engine,"is_trained",True) is False: raise ValueError("Supplied classifier is untrained; pass train_if_needed=True or provide a trained classifier")
    synthetic_missing = master_status == "missing" or training_status == "missing"
    if synthetic_missing:
        synthetic_result=_unavailable("not_evaluated","Valid synthetic benchmark data is unavailable.",{"valid":False,"errors":synthetic_errors},evaluation_time)
    elif synthetic_errors:
        synthetic_result=_unavailable("invalid_test_set","Synthetic benchmark failed validation.",{"valid":False,"errors":synthetic_errors},evaluation_time)
    elif not synthetic:
        synthetic_result=_unavailable("not_evaluated","Valid synthetic benchmark data is unavailable.",{"valid":False,"errors":["No held-out synthetic records available"]},evaluation_time)
    else:
        synthetic_result=_with_targets(_metrics(synthetic,engine)); synthetic_result.update(status="synthetic_benchmark",evaluation_type="synthetic_benchmark",dataset_size=len(synthetic),test_set_size=len(synthetic),evaluation_dataset="Development Synthetic Benchmark: data/dataset.json remainder excluding data/train_split.json",evaluated_at=evaluation_time,evaluation_timestamp=evaluation_time,validation={"valid":True,"errors":[]},provenance="Procedurally generated development data; not OIL field validation or expert-reviewed performance.",message="Quantitative benchmark on synthetic development data")
    if formal_status=="missing" or (formal_status=="ok" and not formal_records):
        formal_result=_unavailable("not_evaluated","An independently expert-reviewed test set is not currently available.",{"valid":False,"errors":formal_read_errors or ["expert_reviewed_test.json is missing or empty"]},evaluation_time)
    elif formal_status!="ok":
        formal_result=_unavailable("invalid_test_set","Expert-reviewed test set could not be read.",{"valid":False,"errors":formal_read_errors},evaluation_time)
    else:
        formal_errors=validate_expert_records(formal_records,training_ids)
        if formal_errors: formal_result=_unavailable("invalid_test_set","Expert-reviewed test set failed validation.",{"valid":False,"errors":formal_errors},evaluation_time)
        else:
            formal_result=_with_targets(_metrics(formal_records,engine,True)); formal_result.update(status="evaluated",evaluation_type="expert_reviewed",dataset_size=len(formal_records),test_set_size=len(formal_records),evaluation_dataset="data/expert_reviewed_test.json",evaluated_at=evaluation_time,evaluation_timestamp=evaluation_time,validation={"valid":True,"errors":[]},provenance="Independently supplied expert-reviewed test set; provenance metadata is declared by the data supplier.",message="Measured on independently expert-reviewed labelled records")
    if formal_result["status"]=="evaluated": primary=formal_result
    elif formal_result["status"]=="invalid_test_set": primary=_unavailable("invalid_test_set","Expert-reviewed test set failed validation; synthetic benchmark is reported separately.",formal_result["validation"],evaluation_time)
    else: primary=synthetic_result
    return {**primary,"model_version":MODEL_VERSION,"synthetic_benchmark":synthetic_result,"formal_evaluation":formal_result,"formal_evaluation_available":formal_result["status"]=="evaluated"}


def run_evaluation() -> Dict[str, Any]:
    return evaluate_classifier(Path(__file__).parent)
