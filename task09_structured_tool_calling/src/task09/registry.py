import asyncio
import json
from dataclasses import dataclass
from typing import Any, Callable, Type

from pydantic import BaseModel, ValidationError

from .schemas import CalculatorArgs, SearchArgs, SqlArgs, WeatherArgs
from .tools import calculator, safe_sql, weather, web_search

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: Type[BaseModel]
    function: Callable[[Any], Any]

    def openai_schema(self) -> dict[str, Any]:
        schema = self.args_model.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "strict": True,
                "parameters": schema,
            },
        }

class ToolRegistry:
    def __init__(self) -> None:
        self._tools = {
            "calculator": ToolSpec("calculator", "Evaluate a safe arithmetic expression.", CalculatorArgs, calculator),
            "weather": ToolSpec("weather", "Get deterministic demo weather for a city; not live data.", WeatherArgs, weather),
            "web_search": ToolSpec("web_search", "Return deterministic mock search results.", SearchArgs, web_search),
            "safe_sql": ToolSpec("safe_sql", "Read fixed demo user rows; does not accept arbitrary SQL.", SqlArgs, safe_sql),
        }

    def names(self) -> list[str]:
        return list(self._tools)

    def definitions(self) -> list[dict[str, Any]]:
        return [spec.openai_schema() for spec in self._tools.values()]

    async def execute(self, name: str, raw_arguments: str | dict[str, Any]) -> str:
        spec = self._tools.get(name)
        if spec is None:
            return json.dumps({"ok": False, "error": f"Tool '{name}' is not allow-listed"})

        try:
            if isinstance(raw_arguments, str):
                args_obj = json.loads(raw_arguments)
            else:
                args_obj = raw_arguments
            args = spec.args_model.model_validate(args_obj)
            # Tools here are lightweight synchronous functions. Move execution off-loop
            # so the same pattern remains responsive if a tool becomes blocking I/O.
            result = await asyncio.to_thread(spec.function, args)
            return json.dumps({"ok": True, "result": result}, ensure_ascii=False)
        except (json.JSONDecodeError, ValidationError, ValueError, TypeError) as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
        except Exception:
            # Avoid leaking stack traces/secrets to the model or end user.
            return json.dumps({"ok": False, "error": "Tool execution failed unexpectedly"})
