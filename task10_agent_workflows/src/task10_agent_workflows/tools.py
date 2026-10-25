from __future__ import annotations

import ast
import operator
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class ToolResult:
    name: str
    output: str

KNOWLEDGE_BASE = [
    "State graphs represent workflows as named nodes connected by explicit edges.",
    "Conditional routing chooses the next node using current state and verification results.",
    "Checkpointing serializes in-progress state so a paused workflow can resume.",
    "Human-in-the-loop approval gates should pause before high-impact actions.",
    "Iteration limits and fallback paths prevent endless retry cycles.",
]

def retrieve(query: str, limit: int = 3) -> list[str]:
    terms = {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", query)}
    scored = []
    for item in KNOWLEDGE_BASE:
        score = sum(term in item.lower() for term in terms)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1]))
    return [item for _, item in scored[:limit]] or [KNOWLEDGE_BASE[0]]

_ALLOWED_BINOPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}

def safe_calculate(expression: str) -> int | float:
    """Evaluate arithmetic expressions using a strict AST allow-list."""
    if len(expression) > 100:
        raise ValueError("Expression is too long")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(right) > 8:
                raise ValueError("Exponent is too large")
            result = _ALLOWED_BINOPS[type(node.op)](left, right)
            if abs(result) > 10**12:
                raise ValueError("Result exceeds safety limit")
            return result
        if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
            return _ALLOWED_UNARY[type(node.op)](visit(node.operand))
        raise ValueError("Only basic arithmetic is allowed")

    return visit(ast.parse(expression, mode="eval"))

def execute_tool(name: str, argument: str) -> ToolResult:
    if name == "calculator":
        return ToolResult(name, str(safe_calculate(argument)))
    if name == "retrieve":
        return ToolResult(name, "\n".join(retrieve(argument)))
    if name == "simulate_destructive_action":
        return ToolResult(name, f"SIMULATED ONLY: would perform action '{argument}'. No external action was taken.")
    raise ValueError(f"Tool is not allow-listed: {name}")
