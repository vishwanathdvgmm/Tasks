import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

async def parse_with_retries(
    raw: str,
    model: type[T],
    *,
    repair: Callable[[str, str, dict], Awaitable[str]] | None = None,
    max_attempts: int = 3,
) -> T:
    """Parse JSON and validate it; optionally ask a provider to repair invalid output.

    `max_attempts` includes the first parse. Retries are bounded to prevent loops.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    current = raw
    last_error = "Unknown validation error"

    for attempt in range(max_attempts):
        try:
            # model_validate_json rejects malformed JSON and validates schema in one step.
            return model.model_validate_json(current)
        except (ValidationError, ValueError, json.JSONDecodeError) as exc:
            last_error = str(exc)
            if attempt == max_attempts - 1 or repair is None:
                break
            current = await repair(
                current,
                last_error,
                model.model_json_schema(),
            )
    raise ValueError(f"Could not produce valid {model.__name__} after {max_attempts} attempt(s): {last_error}")
