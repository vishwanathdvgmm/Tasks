import pytest
from pydantic import ValidationError
from task09.schemas import AnswerEnvelope

def test_valid_answer_envelope():
    obj = AnswerEnvelope(answer="ok", confidence="high", sources=["unit test"])
    assert obj.confidence == "high"

def test_rejects_extra_fields():
    with pytest.raises(ValidationError):
        AnswerEnvelope.model_validate({"answer": "ok", "confidence": "high", "surprise": 1})

def test_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        AnswerEnvelope.model_validate({"answer": "ok", "confidence": "certain"})
