import os
import json
import numpy as np
from typing import Dict, Any, List, Optional
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression

from sentinelsif.preprocessor import TextPreprocessor
from sentinelsif.energy_detector import EnergyDetector
from sentinelsif.control_detector import ControlDetector
from sentinelsif.lsr_tagger import LSRTagger
from sentinelsif.precursor_extractor import PrecursorExtractor

MODEL_VERSION = "SentinelSIF-v2.1-prototype"

class SentinelClassifier:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', sif_confidence_threshold: float = 0.55):
        """
        Args:
            model_name: Sentence-transformer model for embeddings.
            sif_confidence_threshold: Reports with confidence below this threshold
                                      are routed to human-review queue (needs_review=True).
                                      Per PRD FR-3.3.
        """
        self.preprocessor = TextPreprocessor()
        self.energy_detector = EnergyDetector()
        self.control_detector = ControlDetector()
        self.lsr_tagger = LSRTagger()
        self.precursor_extractor = PrecursorExtractor()
        self.sif_confidence_threshold = sif_confidence_threshold
        
        # The rules pipeline remains fully usable when an embedding model is not
        # available locally (for example, on a clean offline prototype install).
        try:
            print("Loading local sentence-transformer model:", model_name)
            self.embedding_model = SentenceTransformer(model_name)
        except Exception as exc:
            print(f"Embedding model unavailable; using explainable rules fallback: {exc}")
            self.embedding_model = None
        self.ml_classifier: Optional[LogisticRegression] = None
        self.is_trained = False

    def train_on_data(self, dataset_path: str = "data/train_split.json"):
        if not os.path.exists(dataset_path):
            print(f"Dataset path {dataset_path} not found. Skipping ML head training.")
            return

        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if self.embedding_model is None:
            return
        texts = [self.preprocessor.preprocess(item["narrative"]) for item in data]
        labels = [1 if item["ground_truth"]["sif_potential"] else 0 for item in data]

        print(f"Encoding {len(texts)} training samples for embedding classifier...")
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)

        # The supplied development split has no independent calibration set.
        # Keep the existing logistic head and expose its output only as a
        # decision-support signal, not as a measured field probability.
        self.ml_classifier = LogisticRegression(C=1.0, max_iter=500)
        self.ml_classifier.fit(embeddings, labels)
        self.is_trained = True
        print("Sentence-Transformer + LogisticRegression ML head trained successfully.")

    def analyze_report(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes a single safety report record:
        {
          "report_id": "...",
          "narrative": "...",
          "site": "...",
          "activity": "...",
          "filer_severity": "...",
          "report_type": "..."
        }
        Returns full SentinelSIF diagnostic result with confidence, evidence, LSR tags, discrepancy flag.
        """
        narrative = record.get("narrative", "")
        site = record.get("site", "Unspecified Site")
        activity = record.get("activity", "Unspecified Activity")
        filer_severity = record.get("filer_severity", "Low")
        report_type = record.get("report_type", "UA/UC")

        cleaned_text = self.preprocessor.preprocess(narrative)

        # 1. Energy Source Detection
        energy_cat, energy_conf, energy_spans = self.energy_detector.detect(cleaned_text)

        # 2. Control Status Detection
        control_status, control_conf, control_spans = self.control_detector.detect(cleaned_text)

        # 3. SIF Potential Decision (Rule-informed energy + control co-occurrence)
        has_high_energy = (energy_cat != "None")
        control_failed = (control_status in ["not_followed", "absent"])
        control_unknown = (control_status == "unknown")
        rule_sif_call = (has_high_energy and control_failed)

        # 4. ML Embedding Score
        ml_prob = 0.50
        if self.is_trained and self.embedding_model is not None and self.ml_classifier is not None and cleaned_text:
            emb = self.embedding_model.encode([cleaned_text], show_progress_bar=False)
            probs = self.ml_classifier.predict_proba(emb)[0]
            ml_prob = float(probs[1])

        # 5. Combine rule-informed decomposition with embedding score.
        if rule_sif_call:
            sif_potential = True
            # Blend rule-based signals (energy + control confidence) with ML probability
            rule_signal = (energy_conf + control_conf) / 2.0
            confidence = round(0.55 * rule_signal + 0.45 * ml_prob, 3)
        elif has_high_energy and control_unknown:
            # Energy present but no clear control signal — lean on ML probability
            # If ML is confident, go with it; otherwise flag for review
            sif_potential = (ml_prob >= 0.60)
            confidence = round(0.30 * energy_conf + 0.70 * ml_prob, 3)
        else:
            # No high energy, or control was explicitly followed
            sif_potential = False
            # Confidence in non-SIF decision
            non_sif_signal = (1.0 - ml_prob)
            if not has_high_energy:
                confidence = round(0.40 * non_sif_signal + 0.60 * (1.0 - energy_conf), 3)
            else:
                # High energy but controls followed — moderate confidence
                confidence = round(0.50 * non_sif_signal + 0.50 * control_conf, 3)

        # Clamp confidence to [0.30, 0.99] — allow low confidence for threshold routing
        confidence = float(np.clip(confidence, 0.30, 0.99))

        # 6. Needs Review flag (FR-3.3): route low-confidence reports to human queue
        needs_review = (confidence < self.sif_confidence_threshold)

        # 7. LSR Multi-Label Tagging
        lsr_tags = self.lsr_tagger.tag(cleaned_text)

        # 8. Precursor Pattern Extraction
        precursor = self.precursor_extractor.extract(cleaned_text, site, activity, control_status)

        # 9. Discrepancy Detection (Filer tagged Low/Medium, but AI flagged SIF Potential)
        is_discrepancy = False
        if sif_potential and filer_severity in ["Low", "Medium"]:
            is_discrepancy = True

        # Combine evidence spans and keep the decision explanation separate from
        # raw regex matches so clients can present an audit-friendly rationale.
        all_evidence = []
        if energy_spans:
            all_evidence.append(f"Energy Cue [{energy_cat}]: " + ", ".join(energy_spans))
        if control_spans:
            all_evidence.append(f"Control Cue [{control_status}]: " + ", ".join(control_spans))
        for tag_item in lsr_tags:
            if tag_item["evidence"]:
                all_evidence.append(f"LSR Span [{tag_item['rule']}]: " + ", ".join(tag_item["evidence"]))

        if sif_potential:
            decision_rationale = (
                f"SIF-Potential: {energy_cat} energy exposure was detected together with "
                f"a direct control that was {control_status.replace('_', ' ')}."
            )
        elif has_high_energy and control_status == "followed":
            decision_rationale = "Non-SIF: high energy was identified, but the narrative indicates direct controls were followed."
        elif not has_high_energy:
            decision_rationale = "Non-SIF: no credible high-energy exposure was detected; procedural non-compliance alone is insufficient."
        else:
            decision_rationale = "Non-SIF pending review: energy was identified but no failed or absent direct control was evidenced."

        return {
            "report_id": record.get("report_id", "OIL-TEMP"),
            "timestamp": record.get("timestamp", "2026-09-04T00:00:00Z"),
            "narrative": narrative,
            "site": precursor["site"],
            "activity": precursor["activity"],
            "report_type": report_type,
            "filer_severity": filer_severity,
            "sif_potential": sif_potential,
            "confidence_score": confidence,
            "model_probability": round(ml_prob, 3),
            "confidence_note": "Decision-support confidence; not a measured field accuracy percentage.",
            "needs_review": needs_review,
            "energy_source": energy_cat,
            "control_status": control_status,
            "barrier_failure_category": precursor["barrier_failure_category"],
            "life_saving_rules": lsr_tags,
            "primary_lsr": lsr_tags[0]["rule"] if lsr_tags else "None",
            "evidence_spans": all_evidence,
            "decision_rationale": decision_rationale,
            "is_discrepancy": is_discrepancy,
            "human_override": False,
            "override_history": [],
            "reviewer_notes": "",
            "model_version": MODEL_VERSION
        }
