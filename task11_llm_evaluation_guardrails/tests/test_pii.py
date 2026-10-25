from task11_guardrails.pii import redact_pii


def test_redacts_email_and_ssn():
    text, counts = redact_pii("Contact alex@example.com; SSN 123-45-6789")
    assert "alex@example.com" not in text
    assert "123-45-6789" not in text
    assert "<EMAIL_1>" in text
    assert "<SSN_1>" in text
    assert counts == {"EMAIL": 1, "SSN": 1}

def test_does_not_change_plain_text():
    text, counts = redact_pii("What is RAG?")
    assert text == "What is RAG?"
    assert counts == {}
