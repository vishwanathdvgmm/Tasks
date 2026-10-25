import json
import os
import re
from dataclasses import dataclass
from typing import Any

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: str

@dataclass
class ModelReply:
    content: str | None
    tool_calls: list[ToolCall]
    raw_message: Any = None

class MockProvider:
    """Predictable provider for tests and demos; it does not call an LLM."""

    def __init__(self) -> None:
        self._turn = 0
        self._pending_calls: list[ToolCall] = []

    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelReply:
        last = messages[-1]
        if last["role"] == "tool":
            # Once all parallel tool results are appended, synthesize a final answer.
            tool_messages = [m for m in messages if m["role"] == "tool"]
            parsed = []
            for m in tool_messages[-4:]:
                try:
                    parsed.append(json.loads(m["content"]))
                except json.JSONDecodeError:
                    parsed.append({"ok": False, "error": "Unreadable tool result"})
            return ModelReply(
                content=json.dumps({
                    "answer": f"Tool execution completed. Results: {json.dumps(parsed, ensure_ascii=False)}",
                    "confidence": "high",
                    "sources": ["mock tool execution"],
                }),
                tool_calls=[],
            )

        prompt = str(last.get("content", ""))
        low = prompt.lower()
        calls: list[ToolCall] = []

        # Generate multiple independent calls for the parallel demo.
        if "parallel" in low or ("weather" in low and "bengaluru" in low and "london" in low):
            calls = [
                ToolCall("call_weather_1", "weather", json.dumps({"city": "Bengaluru"})),
                ToolCall("call_weather_2", "weather", json.dumps({"city": "London"})),
            ]
        elif "weather" in low:
            city = "Bengaluru" if "bengaluru" in low else ("London" if "london" in low else "Tokyo")
            calls = [ToolCall("call_weather_1", "weather", json.dumps({"city": city}))]
        elif "search" in low:
            calls = [ToolCall("call_search_1", "web_search", json.dumps({"query": prompt[:180]}))]
        elif "sql" in low or "database" in low or "users" in low:
            calls = [ToolCall("call_sql_1", "safe_sql", json.dumps({"query_name": "demo_users"}))]
        elif "calculate" in low or re.search(r"\d+\s*[\+\-\*/]\s*\d+", low):
            expr = re.sub(r"(?i)^.*?calculate\s+", "", prompt).strip(" ?.")
            match = re.search(r"[\d\s().+\-*/%]+", expr)
            expr = match.group(0).strip() if match else "19 * 23"
            calls = [ToolCall("call_calc_1", "calculator", json.dumps({"expression": expr}))]
        if calls:
            return ModelReply(content=None, tool_calls=calls)
        return ModelReply(
            content=json.dumps({
                "answer": "Mock provider response. Try a calculator, weather, search, SQL, or parallel request.",
                "confidence": "medium",
                "sources": [],
            }),
            tool_calls=[],
        )

    async def structured(self, prompt: str, schema: dict[str, Any]) -> str:
        # Deliberately returns a valid object conforming to the project's AnswerEnvelope.
        return json.dumps({
            "answer": f"Structured mock response for: {prompt}",
            "confidence": "medium",
            "sources": ["mock provider"],
        })

class OpenAIProvider:
    """Optional adapter using OpenAI Chat Completions APIs."""

    def __init__(self, model: str | None = None) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("Install the OpenAI extra: uv sync --extra openai") from exc
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("Set OPENAI_API_KEY before using the OpenAI provider")
        self.client = AsyncOpenAI()
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> ModelReply:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=True,
        )
        message = response.choices[0].message
        calls = [
            ToolCall(tc.id, tc.function.name, tc.function.arguments)
            for tc in (message.tool_calls or [])
        ]
        return ModelReply(
            content=message.content,
            tool_calls=calls,
            raw_message=message,
        )

    async def structured(self, prompt: str, schema: dict[str, Any]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return an answer that follows the supplied schema."},
                {"role": "user", "content": prompt},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "answer_envelope",
                    "strict": True,
                    "schema": schema,
                },
            },
        )
        content = response.choices[0].message.content
        if not content:
            raise RuntimeError("Model returned no structured content")
        return content
