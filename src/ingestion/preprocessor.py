"""Medical text preprocessor: PII anonymization, abbreviation expansion."""
from __future__ import annotations
import re

# Common medical abbreviations
ABBREVIATIONS = {
    "BP": "blood pressure", "HR": "heart rate", "RR": "respiratory rate",
    "T": "temperature", "SpO2": "oxygen saturation", "ECG": "electrocardiogram",
    "CBC": "complete blood count", "BMP": "basic metabolic panel",
    "CT": "computed tomography", "MRI": "magnetic resonance imaging",
    "PRN": "as needed", "QID": "four times daily", "TID": "three times daily",
    "BID": "twice daily", "QD": "once daily", "NPO": "nothing by mouth",
    "SOB": "shortness of breath", "CP": "chest pain", "HA": "headache",
    "HTN": "hypertension", "DM": "diabetes mellitus", "CAD": "coronary artery disease",
    "CHF": "congestive heart failure", "COPD": "chronic obstructive pulmonary disease",
    "UTI": "urinary tract infection", "URI": "upper respiratory infection",
}

PII_PATTERNS = [
    (r"\d{3}-\d{2}-\d{4}",   "[SSN]"),
    (r"\d{10}",               "[PHONE]"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", "[EMAIL]"),
    (r"\d{1,5}\s+\w+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr)", "[ADDRESS]"),
    (r"DOB:\s*\d{1,2}/\d{1,2}/\d{2,4}", "DOB: [DATE]"),
]


class MedicalPreprocessor:
    """Cleans and normalises medical text before LLM processing."""

    def __init__(self, expand_abbreviations: bool = True,
                 anonymize_pii: bool = True) -> None:
        self.expand_abbr = expand_abbreviations
        self.anonymize   = anonymize_pii

    def process(self, text: str) -> str:
        text = self._normalise_whitespace(text)
        if self.anonymize:
            text = self._anonymize_pii(text)
        if self.expand_abbr:
            text = self._expand_abbreviations(text)
        return text.strip()

    def _normalise_whitespace(self, text: str) -> str:
        text = re.sub(r"
{3,}", "

", text)
        text = re.sub(r" {2,}", " ", text)
        return text

    def _anonymize_pii(self, text: str) -> str:
        for pattern, replacement in PII_PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _expand_abbreviations(self, text: str) -> str:
        for abbr, expansion in ABBREVIATIONS.items():
            pattern = r"" + re.escape(abbr) + r""
            text = re.sub(pattern, f"{abbr} ({expansion})", text, count=1)
        return text

# 11:53:31 — feat: add chunk overlap configuration for context preservati

# 11:53:31 — docs: document chunking strategy decisions in docs/chunking.

# 11:15:23 — fix: remove unused import in preprocessor

# 11:25:06 — style: reorder imports alphabetically in preprocessor

# 11:05:49 — docs: fix typo in inline comment in preprocessor

# 12:11:08 — style: run black formatter on preprocessor

# 11:08:25 — docs: update example in docstring of preprocessor

# 12:31:10 — refactor: rename variable for clarity in preprocessor

# 12:28:25 — fix: handle None input edge case in preprocessor

# 11:19:48 — docs: fix typo in inline comment in preprocessor

# 12:50:26 — docs: add module docstring to preprocessor

# 12:50:26 — chore: add logging statement to preprocessor
