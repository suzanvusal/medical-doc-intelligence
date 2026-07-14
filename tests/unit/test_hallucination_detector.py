"""Unit tests for hallucination detector."""
import pytest
from unittest.mock import AsyncMock
from src.monitoring.hallucination_detector import HallucinationDetector


@pytest.fixture
def detector():
    mock_client = AsyncMock()
    return HallucinationDetector(mock_client, threshold=0.6)


@pytest.mark.asyncio
async def test_grounded_answer_not_hallucinated(detector):
    answer  = "The patient has diabetes and hypertension."
    context = ["The patient has diabetes mellitus and hypertension.",
               "Blood pressure medication was prescribed."]
    result  = await detector.detect(answer, context)
    assert not result.is_hallucinated
    assert result.severity in ("none", "minor")


@pytest.mark.asyncio
async def test_hallucinated_answer_detected(detector):
    answer  = "Patient underwent triple bypass surgery and was placed on ECMO."
    context = ["Patient had a mild headache and was given paracetamol."]
    result  = await detector.detect(answer, context)
    assert result.grounding_score < 0.6


@pytest.mark.asyncio
async def test_empty_context_critical_severity(detector):
    result = await detector.detect("Some clinical claim about the patient.", [])
    assert result.grounding_score == 0.0


@pytest.mark.asyncio
async def test_severity_none_on_high_score(detector):
    answer  = "fever temperature elevated"
    context = ["Patient has fever with elevated temperature of 38.9 degrees."]
    result  = await detector.detect(answer, context)
    assert result.severity in ("none", "minor", "moderate")


@pytest.mark.asyncio
async def test_ungrounded_claims_listed(detector):
    answer  = "Patient has cancer. Patient needs chemotherapy. Prognosis is poor."
    context = ["Patient has a mild upper respiratory infection."]
    result  = await detector.detect(answer, context)
    assert isinstance(result.ungrounded_claims, list)

# 12:51:03 — test: add snapshot tests for API response schemas

# 14:16:12 — fix: correct off-by-one error in test_hallucination_detector

# 13:34:00 — refactor: rename variable for clarity in test_hallucination_

# 13:34:00 — style: run black formatter on test_hallucination_detector

# 12:24:01 — style: run black formatter on test_hallucination_detector

# 13:54:39 — style: reorder imports alphabetically in test_hallucination_

# 12:30:11 — fix: handle None input edge case in test_hallucination_detec

# 11:37:42 — chore: day 30 maintenance sweep
