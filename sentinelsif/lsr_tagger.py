import re
from typing import List, Dict, Any

LSR_TAXONOMY = {
    "Energy Isolation": [
        r'\b(isolation|loto|lockout|tagout|valve not locked|de-energise|de-energized|breaker|live busbar|mcc|415v|electrical panel)\b'
    ],
    "Hot Work": [
        r'\b(welding|hot work|gas test|flammable|fire watch|grinding|spark|ignition|hydrocarbon line|pipe welding)\b'
    ],
    "Confined Space": [
        r'\b(confined space|tank entry|vessel entry|sump pit|oxygen level|gas monitoring|attendant|standby)\b'
    ],
    "Line of Fire": [
        r'\b(suspended load|pinch point|line of fire|struck-by|moving equipment|underneath load|excavation trench|mud pump belt)\b',
        r'\b(?:workers?|personnel) (?:below|beneath|under) (?:the |a )?(?:suspended )?(?:load|object|component)|exclusion zone (?:was )?(?:not maintained|breached)|dropped[- ]object|load swing\b'
    ],
    "Working at Height": [
        r'\b(work at height|working at height|fall arrest|harness|scaffold|monkey board|derrick|edge protection|ladder|platform|roof)\b'
    ],
    "Driving": [
        r'\b(driving|speeding|seatbelt|mobile phone|journey management|ivms|tanker driver|road|overtaking)\b'
    ],
    "Lifting Operations": [
        r'\b(lifting|lift plan|sling|swl|crane|rigger|hoist|suspended pipe|bop stack lift)\b',
        r'\b(?:heavy|suspended) (?:load|component)|lifting (?:equipment|gear|operation)|hoisting|load handling\b'
    ],
    "Management of Change": [
        r'\b(management of change|moc|temporary bypass|modification|deviation from design|unauthorized change)\b'
    ],
    "Safe Mechanical Lifting": [
        r'\b(lifting gear|uncertified equipment|overload|winch|workover rig lift|rated sling)\b',
        r'\bdefective lifting (?:equipment|gear)|(?:lifting equipment|lifting gear) (?:had )?not been verified|inspection defect\b'
    ],
    "Permit to Work": [
        r'\b(permit to work|ptw|valid permit|work outside permit|permit scope|unpermitted)\b'
    ],
    "Bypassing Safety Controls": [
        r'\b(bypassed|bypass|guard removed|interlock defeated|safety override|disabled alarm|circumvented|defeated interlock|overrode safety|removed guard|safety device disabled|interlock bypassed)\b'
    ]
}

class LSRTagger:
    def __init__(self):
        self.compiled = {
            rule: [re.compile(p, re.IGNORECASE) for p in pat_list]
            for rule, pat_list in LSR_TAXONOMY.items()
        }

    def tag(self, text: str) -> List[Dict[str, Any]]:
        """
        Multi-label tagging for 10 IOGP Life-Saving Rules.
        Returns list of dicts: [{"rule": ..., "confidence": ..., "evidence": [...]}]
        """
        results = []
        for rule, regexes in self.compiled.items():
            matched_spans = []
            for rx in regexes:
                for m in rx.finditer(text):
                    matched_spans.append(m.group(0))
            if matched_spans:
                conf = min(0.96, 0.65 + len(matched_spans) * 0.15)
                results.append({
                    "rule": rule,
                    "confidence": round(conf, 2),
                    "evidence": list(set(matched_spans))
                })
        
        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results
