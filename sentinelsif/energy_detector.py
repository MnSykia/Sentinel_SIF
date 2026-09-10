import re
from typing import Dict, List, Tuple

ENERGY_PATTERNS = {
    "Gravity": [
        r'\b(height|scaffold|derrick|monkey board|ladder|roof|suspended load|crane|hoist|lifting|dropped object|fall|18 meters|12m|platform)\b',
        r'\b(pipe bundle|drill collar|bop stack|sling|rig floor)\b',
        # Load-handling language used in field narratives; these describe a
        # credible gravity exposure, not merely an administrative activity.
        r'\b(suspended (?:load|object|component)|(?:heavy|lifted|raised|overhead) (?:load|component|object)|lifting (?:operation|equipment|gear)|load handling|hoisting|dropped[- ]object potential|falling object|object falling|load swing|stored mechanical energy)\b',
        r'\b(?:load|object|component) (?:above|over) (?:personnel|workers|the work area)|(?:workers?|personnel) (?:below|beneath|under) (?:a |the )?(?:suspended )?(?:load|object|component)\b'
    ],
    "Pressure": [
        r'\b(pressure|psi|manifold|valve|flange|separator|header|compressor|blowout|bop|hydrocarbon line|pipeline|condensate|trapped energy|bleed)\b',
        r'\b(600 psi|450 psi|bar)\b'
    ],
    "Mechanical": [
        r'\b(rotating|mud pump|drive belt|pinch point|machine guard|shaft|flywheel|grinding|torqueing|sheave)\b'
    ],
    "Electrical": [
        r'\b(electrical|415v|mcc|busbar|sub-station|transformer|live wire|breaker|switchgear|arc flash|voltage)\b'
    ],
    "Chemical/Thermal": [
        r'\b(welding|hot work|hydrocarbon|flammable|gas|h2s|tank cleaning|vapor|ignition|fire|sump|crude storage)\b'
    ],
    "Motion/Vehicle": [
        r'\b(tanker|driver|driving|speeding|km/h|haulage|traffic|vehicle|ivms|road|overtaking|mobile equipment|forklift)\b'
    ]
}

class EnergyDetector:
    def __init__(self):
        self.patterns = {cat: [re.compile(p, re.IGNORECASE) for p in pat_list] 
                         for cat, pat_list in ENERGY_PATTERNS.items()}

    def detect(self, text: str) -> Tuple[str, float, List[str]]:
        """
        Detects primary energy source, returns (category, confidence, evidence_spans).
        If no high energy detected, returns ("None", 0.10, [])
        """
        text_lower = text.lower()
        scores = {}
        spans = {}

        for category, regexes in self.patterns.items():
            matches = []
            for rx in regexes:
                for match in rx.finditer(text):
                    matches.append(match.group(0))
            if matches:
                scores[category] = len(matches) * 0.35 + 0.50
                spans[category] = list(set(matches))

        if not scores:
            return "None", 0.10, []

        # Get highest scoring category
        best_cat = max(scores.items(), key=lambda x: x[1])[0]
        confidence = min(0.98, scores[best_cat])
        evidence = spans[best_cat]
        
        return best_cat, confidence, evidence
