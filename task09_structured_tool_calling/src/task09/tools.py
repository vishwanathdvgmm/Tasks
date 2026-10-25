import ast
import operator
import re
from typing import Any

from .schemas import CalculatorArgs, SearchArgs, SqlArgs, WeatherArgs

# Deliberately limited arithmetic evaluator: no eval(), names, attributes, or function calls.
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def _eval_arithmetic(node: ast.AST) -> float | int:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        if abs(node.value) > 10**12:
            raise ValueError("Numeric literal is too large")
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        left, right = _eval_arithmetic(node.left), _eval_arithmetic(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 8:
            raise ValueError("Exponent magnitude must be at most 8")
        value = _BINOPS[type(node.op)](left, right)
        if isinstance(value, complex) or abs(value) > 10**15:
            raise ValueError("Result is outside the allowed range")
        return value
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_arithmetic(node.operand))
    raise ValueError("Only numeric literals and +, -, *, /, //, %, ** are supported")

def calculator(args: CalculatorArgs) -> dict[str, Any]:
    try:
        tree = ast.parse(args.expression, mode="eval")
        result = _eval_arithmetic(tree.body)
        return {"expression": args.expression, "result": result}
    except (SyntaxError, ZeroDivisionError, OverflowError, ValueError) as exc:
        raise ValueError(f"Invalid arithmetic expression: {exc}") from exc

def weather(args: WeatherArgs) -> dict[str, Any]:
    # Stable fixture, not a live weather service.
    city = args.city.strip().title()
    demo = {
        "Bengaluru": {"temperature_c": 27, "condition": "Partly cloudy"},
        "London": {"temperature_c": 14, "condition": "Light rain"},
        "Tokyo": {"temperature_c": 21, "condition": "Cloudy"},
    }
    return {"city": city, **demo.get(city, {"temperature_c": None, "condition": "No demo data"})}

def web_search(args: SearchArgs) -> dict[str, Any]:
    # Mock results make this demo deterministic; no external web request is made.
    q = args.query.strip()
    return {
        "query": q,
        "results": [
            {"title": f"Demo result for: {q}", "snippet": "This is a deterministic mock search result."}
        ],
        "provider": "mock",
    }

def safe_sql(args: SqlArgs) -> dict[str, Any]:
    # Intentionally fixed query and in-memory fixture. Never interpolate model SQL.
    if args.query_name != "demo_users":
        raise ValueError("Only query_name='demo_users' is allowed")
    return {
        "query_name": "demo_users",
        "rows": [
            {"id": 1, "name": "Ada", "active": True},
            {"id": 2, "name": "Grace", "active": True},
        ],
        "note": "Fixture data; no database connection was opened.",
    }
