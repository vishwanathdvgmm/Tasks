import pytest
from pydantic import ValidationError
from app.models import ChatRequest

def test_request_accepts_valid_session():
    request = ChatRequest(session_id="demo_01", message="Hello")
    assert request.memory_strategy == "sliding_window"

def test_request_rejects_key_injection_session():
    with pytest.raises(ValidationError):
        ChatRequest(session_id="x}:messages", message="Hello")

def test_request_rejects_blank_message():
    with pytest.raises(ValidationError):
        ChatRequest(session_id="demo", message=" ")
