import pytest
from task09.retry import parse_with_retries
from task09.schemas import AnswerEnvelope

@pytest.mark.asyncio
async def test_retry_repair_function():
    async def repair(raw, error, schema):
        return '{"answer":"fixed","confidence":"high","sources":[]}'

    result = await parse_with_retries(
        '{"answer":42}', AnswerEnvelope, repair=repair, max_attempts=2
    )
    assert result.answer == "fixed"

@pytest.mark.asyncio
async def test_retry_is_bounded():
    with pytest.raises(ValueError, match="after 2 attempt"):
        await parse_with_retries('not json', AnswerEnvelope, max_attempts=2)
