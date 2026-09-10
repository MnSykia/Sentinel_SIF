import re
from typing import Dict, Any

BARRIER_FAILURES = {
    "LOTO / Energy Isolation Bypassed": [r'loto', r'isolation', r'lockout', r'valve not locked', r'breaker'],
    "Permit to Work (PTW) Non-Compliance": [r'ptw', r'permit', r'unpermitted', r'without permit'],
    "Gas Test Not Performed": [r'gas test', r'gas check', r'gas monitoring', r'0% lel'],
    "Fall Protection / Harness Unhooked": [r'harness', r'fall arrest', r'monkey board', r'scaffold', r'height'],
    "Line of Fire / Standing Under Suspended Load": [r'suspended load', r'line of fire', r'pinch point', r'underneath', r'workers? (?:standing )?(?:below|beneath|under)', r'exclusion zone (?:was )?not maintained'],
    "Inadequate Guarding / Machine Guard Removed": [r'guard removed', r'machine guard', r'live busbar', r'drive belt'],
    "Defective / Unverified Lifting Equipment": [r'defective lifting equipment', r'inspection defect', r'lifting plan (?:was )?not followed', r'lifting equipment (?:had )?not been verified'],
    "Journey Management & Speeding Violation": [r'speeding', r'driving', r'ivms', r'mobile phone', r'tanker driver'],
    "Unauthorized Modification / MOC Ignored": [r'moc', r'modification', r'temporary bypass', r'jugaad']
}

class PrecursorExtractor:
    def __init__(self):
        self.barriers = {
            cat: [re.compile(p, re.IGNORECASE) for p in pat_list]
            for cat, pat_list in BARRIER_FAILURES.items()
        }

    def extract(self, text: str, site_meta: str = "", activity_meta: str = "", control_status: str = "followed") -> Dict[str, Any]:
        """
        Extracts activity, location/site, and barrier failure category.
        """
        site = site_meta if site_meta else "General Field Operations"
        activity = activity_meta if activity_meta else "General Maintenance"
        
        if control_status == "followed":
            barrier = "None"
        else:
            barrier = "Other / Procedure Violation"
            for cat, regexes in self.barriers.items():
                if any(rx.search(text) for rx in regexes):
                    barrier = cat
                    break

        return {
            "site": site,
            "activity": activity,
            "barrier_failure_category": barrier
        }
