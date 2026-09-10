import re
from typing import Tuple, List

CONTROL_PATTERNS = {
    "absent": [
        r'\b(without loto|without ptw|without permit|no permit|guard removed|unlocked|no gas|no harness|without fall arrest|standby absent|no tagline|no utility map|live busbar exposed|unprotected)\b',
        r'\b(bina ptw|bina permit|lockout tagout chhod|gas testing missing|safety belt nahi)\b',
        r'\bwithout (?:verifying |verified |effective )?(?:loto|lock ?out tag ?out|isolation|energy isolation)\b',
        r'\b(?:isolation|energy isolation) (?:was |had )?(?:not established|not verified|not confirmed)\b',
        r'\bno effective (?:energy )?isolation (?:was )?confirmed\b',
        r'\bbefore (?:energy )?isolation was verified\b',
        r'\bwithout (?:a )?(?:valid )?(?:gas test|gas monitoring)|no (?:continuous )?gas monitoring|gas test (?:was )?not performed\b',
        r'\bno standby attendant|standby attendant (?:was )?absent\b',
        r'\b(?:fall arrest|edge protection) (?:equipment )?(?:was )?(?:missing|absent)\b'
    ],
    "not_followed": [
        r'\b(bypassed|unhooked|not verified|not complied|not worn|speeding|exceeding speed|mobile phone|not sealed|without approval|temporary bypass|standing under|in pinch point|unrated sling|damaged rail)\b',
        r'\b(tez gaadi|jugaad|neeche khada)\b',
        # Direct controls for load-handling / line-of-fire exposures.
        r'\b(?:exclusion zone|barricad(?:e|ing)) (?:was |were )?(?:not maintained|not in place|not established|inadequate|breached)\b',
        r'\b(?:workers?|personnel) (?:were |was )?(?:standing |working )?(?:below|beneath|under|inside) (?:the |a )?(?:suspended )?(?:load|object|component|exclusion zone)\b',
        r'\b(?:lifting )?plan (?:was |had )?not followed\b',
        r'\b(?:defective|damaged|uninspected) lifting (?:equipment|gear)\b',
        r'\b(?:lifting equipment|lifting gear|equipment condition) (?:had )?not been verified\b',
        r'\b(?:equipment|lifting gear) inspection (?:was |had )?not (?:completed|performed|verified)\b',
        r'\bmachine guard (?:had )?been removed\b'
    ],
    "followed": [
        r'\b(ptw active|loto verified|gas test completed|0% lel|harness hooked|certified crane|lift plan verified|tagline attached|dual lanyard|hard hat secured|handrail|inspected|followed)\b',
        r'\b(?:required )?(?:permit|isolation|ppe|controls?) (?:were )?verified\b',
        r'\bexclusion zone (?:was )?(?:maintained|established|in place)\b'
    ]
}

class ControlDetector:
    def __init__(self):
        self.compiled = {
            status: [re.compile(p, re.IGNORECASE) for p in pat_list]
            for status, pat_list in CONTROL_PATTERNS.items()
        }

    def detect(self, text: str) -> Tuple[str, float, List[str]]:
        """
        Detects direct control status: 'followed', 'not_followed', or 'absent'.
        Returns (status, confidence, evidence_spans)
        """
        text_lower = text.lower()
        
        # Check absent cues first (strongest negative precursor signal)
        absent_spans = []
        for rx in self.compiled["absent"]:
            for m in rx.finditer(text):
                absent_spans.append(m.group(0))
        if absent_spans:
            return "absent", 0.92, list(set(absent_spans))

        # Check not_followed cues
        nf_spans = []
        for rx in self.compiled["not_followed"]:
            for m in rx.finditer(text):
                nf_spans.append(m.group(0))
        if nf_spans:
            return "not_followed", 0.88, list(set(nf_spans))

        # Check followed cues
        f_spans = []
        for rx in self.compiled["followed"]:
            for m in rx.finditer(text):
                f_spans.append(m.group(0))
        if f_spans:
            return "followed", 0.90, list(set(f_spans))

        # Default fallback: no explicit compliance or failure cue found — treat as unknown
        # These reports should be routed to human-review queue rather than auto-classified
        return "unknown", 0.40, ["no explicit control cue detected — requires manual review"]
