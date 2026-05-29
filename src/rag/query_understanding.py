"""Medical query parser and intent detector."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re


class QueryIntent(str, Enum):
    DIAGNOSIS_LOOKUP   = "diagnosis_lookup"
    MEDICATION_CHECK   = "medication_check"
    LAB_RESULT_LOOKUP  = "lab_result_lookup"
    SUMMARY_REQUEST    = "summary_request"
    PROCEDURE_LOOKUP   = "procedure_lookup"
    GENERAL_QUESTION   = "general_question"


INTENT_PATTERNS = {
    QueryIntent.DIAGNOSIS_LOOKUP:  [r"diagnos", r"condition", r"disorder", r"disease"],
    QueryIntent.MEDICATION_CHECK:  [r"medication", r"drug", r"prescri", r"dose", r"mg"],
    QueryIntent.LAB_RESULT_LOOKUP: [r"lab", r"blood test", r"result", r"level", r"value"],
    QueryIntent.SUMMARY_REQUEST:   [r"summar", r"overview", r"brief", r"main points"],
    QueryIntent.PROCEDURE_LOOKUP:  [r"procedure", r"surgery", r"operation", r"treatment"],
}

MEDICAL_ABBREVIATION_MAP = {
    "MI": "myocardial infarction", "CVA": "cerebrovascular accident",
    "DM": "diabetes mellitus", "HTN": "hypertension",
    "CHF": "congestive heart failure", "COPD": "chronic obstructive pulmonary disease",
}


@dataclass
class ParsedQuery:
    original:    str
    rewritten:   str
    intent:      QueryIntent
    keywords:    list[str]
    temporal:    str | None = None


class MedicalQueryParser:
    def parse(self, query: str) -> ParsedQuery:
        rewritten = self._expand_abbreviations(query)
        intent    = self._detect_intent(rewritten)
        keywords  = self._extract_keywords(rewritten)
        temporal  = self._extract_temporal(rewritten)
        return ParsedQuery(original=query, rewritten=rewritten,
                          intent=intent, keywords=keywords, temporal=temporal)

    def _expand_abbreviations(self, text: str) -> str:
        for abbr, expansion in MEDICAL_ABBREVIATION_MAP.items():
            text = re.sub(r"" + abbr + r"", expansion, text, flags=re.IGNORECASE)
        return text

    def _detect_intent(self, text: str) -> QueryIntent:
        text_lower = text.lower()
        for intent, patterns in INTENT_PATTERNS.items():
            if any(re.search(p, text_lower) for p in patterns):
                return intent
        return QueryIntent.GENERAL_QUESTION

    def _extract_keywords(self, text: str) -> list[str]:
        stop = {"what","is","the","a","an","of","for","in","on","at","to","and","or"}
        return [w for w in re.findall(r"\w{3,}", text.lower()) if w not in stop][:10]

    def _extract_temporal(self, text: str) -> str | None:
        patterns = [r"last \d+ (days?|weeks?|months?)", r"past \d+ (days?|weeks?|months?)",
                    r"since \w+", r"between .+ and .+"]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group()
        return None

# 11:25:06 — style: run black formatter on query_understanding

# 11:03:54 — docs: update example in docstring of query_understanding

# 11:03:54 — fix: handle None input edge case in query_understanding

# 12:44:42 — chore: add logging statement to query_understanding

# 12:11:08 — style: reorder imports alphabetically in query_understanding

# 12:28:25 — perf: add __slots__ to dataclass in query_understanding

# 11:19:47 — fix: correct off-by-one error in query_understanding

# 12:50:26 — fix: remove unused import in query_understanding
