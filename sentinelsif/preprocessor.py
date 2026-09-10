import re

HSE_ABBREVIATIONS = {
    r'\bPTW\b': 'permit to work',
    r'\bLOTO\b': 'lock out tag out energy isolation',
    r'\bBOP\b': 'blow out preventer',
    r'\bSWL\b': 'safe working load',
    r'\bPPE\b': 'personal protective equipment',
    r'\bH2S\b': 'hydrogen sulfide toxic gas',
    r'\bLEL\b': 'lower explosive limit gas concentration',
    r'\bDBB\b': 'double block and bleed valve isolation',
    r'\bMOC\b': 'management of change',
    r'\bIVMS\b': 'in vehicle monitoring system driving',
    r'\bMCC\b': 'motor control center electrical panel',
    r'\bCTF\b': 'central tank farm',
    r'\bJSA\b': 'job safety analysis'
}

CODE_MIX_MAPPINGS = {
    r'\bbina PTW\b': 'without permit to work',
    r'\bbina permit\b': 'without permit',
    r'\bsafety belt nahi lagaya\b': 'harness unhooked without fall arrest',
    r'\btez gaadi\b': 'speeding motor vehicle',
    r'\bgaadi\b': 'vehicle tanker driving',
    r'\bgas check missing\b': 'gas test not performed',
    r'\bjugaad\b': 'unauthorized bypass modification',
    r'\bneeche khada\b': 'standing under load line of fire',
    r'\bseedhi\b': 'ladder scaffold height'
}

class TextPreprocessor:
    def __init__(self):
        self.abbreviations = HSE_ABBREVIATIONS
        self.code_mix = CODE_MIX_MAPPINGS

    def preprocess(self, text: str) -> str:
        if not text:
            return ""
        
        cleaned = text.strip()
        
        # Expand HSE Abbreviations
        for pattern, replacement in self.abbreviations.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
            
        # Normalize transliterated / code-mix field terms
        for pattern, replacement in self.code_mix.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
            
        # Standardize extra spaces & lowercasing for embeddings
        cleaned_str = re.sub(r'\s+', ' ', cleaned)
        return cleaned_str
