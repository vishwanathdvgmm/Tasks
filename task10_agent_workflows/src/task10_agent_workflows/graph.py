from __future__ import annotations

import re
import uuid
from collections.abc import Callable
from pathlib import Path

from .checkpoint import CheckpointStore
from .model import MockModel
from .state import AgentState
from .tools import execute_tool, retrieve

Node = Callable[[AgentState], AgentState]

class StateGraph:
    """Small explicit state-graph runner with conditional edges and hard limits."""

    def __init__(self, checkpoint_store: CheckpointStore | None = None, model: MockModel | None = None):
        self.store = checkpoint_store or CheckpointStore()
        self.model = model or MockModel()
        self.nodes: dict[str, Node] = {
            "planner": self.planner,
            "researcher": self.researcher,
            "executor": self.executor,
            "reviewer": self.reviewer,
            "approval_gate": self.approval_gate,
            "output": self.output,
            "fallback": self.fallback,
        }

    @staticmethod
    def graph_description() -> str:
        return (
            "START -> planner -> researcher -> executor -> reviewer\n"
            "reviewer -- revise --> executor\n"
            "reviewer -- pass --> approval_gate -> output -> END\n"
            "any step-limit/revision-limit breach -> fallback\n"
        )

    def planner(self, s: AgentState) -> AgentState:
        s.plan = self.model.plan(s.user_request)
        return s

    def researcher(self, s: AgentState) -> AgentState:
        s.evidence = retrieve(s.user_request, limit=4)
        return s

    def executor(self, s: AgentState) -> AgentState:
        request = s.user_request
        # The dispatcher only invokes pre-approved tools; never runs arbitrary code.
        expressions = re.findall(r"(?<![\w.])(?:\d+(?:\.\d+)?\s*(?:\+|-|\*|/|\*\*)\s*)+\d+(?:\.\d+)?", request)
        for expression in expressions[:3]:
            try:
                result = execute_tool("calculator", expression)
                item = f"{result.name}: {expression} = {result.output}"
                if item not in s.tool_results:
                    s.tool_results.append(item)
            except (ValueError, SyntaxError, ZeroDivisionError) as exc:
                s.errors.append(f"Calculator error: {exc}")
        if re.search(r"delete|transfer|send|destructive|commit", request, re.I):
            result = execute_tool("simulate_destructive_action", "requested high-impact action")
            if result.output not in s.tool_results:
                s.tool_results.append(result.output)
        s.draft = self.model.draft(request, s.evidence, s.tool_results, s.review_feedback)
        return s

    def reviewer(self, s: AgentState) -> AgentState:
        passed, message = self.model.review(s.draft, s.user_request, s.revision_count)
        s.metadata["review_passed"] = passed
        s.metadata["review_message"] = message
        if not passed:
            s.review_feedback.append(message)
            s.revision_count += 1
        return s

    def approval_gate(self, s: AgentState) -> AgentState:
        needs_approval = s.require_approval or bool(re.search(r"delete|transfer|send|destructive|commit", s.user_request, re.I))
        if not needs_approval:
            return s
        if s.approval_decision == "approve":
            s.metadata["approval_status"] = "approved"
            return s
        if s.approval_decision == "reject":
            s.status = "rejected"
            s.final_output = "Workflow rejected by human approval. No external action was performed."
            return s
        s.status = "paused"
        s.approval_id = s.run_id
        return s

    def output(self, s: AgentState) -> AgentState:
        s.status = "completed"
        s.final_output = s.draft
        if s.metadata.get("approval_status") == "approved":
            s.final_output += "\n\nHuman approval: approved. The high-impact action remains simulated; no external system was changed."
        return s

    def fallback(self, s: AgentState) -> AgentState:
        s.status = "failed"
        s.final_output = (
            "The workflow stopped safely after reaching a configured limit. "
            "Please refine the request or inspect the recorded errors and checkpoint."
        )
        return s

    def run(self, request: str, *, require_approval: bool = False, max_steps: int = 12,
            max_revisions: int = 2, run_id: str | None = None) -> AgentState:
        state = AgentState(
            run_id=run_id or uuid.uuid4().hex[:12],
            user_request=request,
            require_approval=require_approval,
            max_steps=max_steps,
            max_revisions=max_revisions,
        )
        return self._drive(state)

    def resume(self, approval_id: str, decision: str) -> AgentState:
        if decision not in {"approve", "reject"}:
            raise ValueError("decision must be 'approve' or 'reject'")
        state = self.store.load(approval_id)
        if state.status != "paused":
            raise ValueError(f"Checkpoint is not paused (status={state.status})")
        state.approval_decision = decision
        state.status = "running"
        state.current_node = "approval_gate"
        return self._drive(state)

    def _drive(self, state: AgentState) -> AgentState:
        while state.status == "running":
            if state.step_count >= state.max_steps:
                state.current_node = "fallback"
            if state.revision_count > state.max_revisions:
                state.current_node = "fallback"
            node_name = state.current_node
            node = self.nodes.get(node_name)
            if node is None:
                state.errors.append(f"Unknown node: {node_name}")
                state.current_node = "fallback"
                node = self.nodes["fallback"]
            state.visited_nodes.append(node_name)
            state.step_count += 1
            try:
                state = node(state)
            except Exception as exc:  # record and safely terminate unexpected node failures
                state.errors.append(f"{node_name}: {type(exc).__name__}: {exc}")
                state.current_node = "fallback"
                if node_name == "fallback":
                    state.status = "failed"
                    state.final_output = "Workflow failed safely."
                    break
                continue

            if state.status == "paused":
                self.store.save(state)
                return state
            if state.status in {"rejected", "completed", "failed"}:
                break

            if node_name == "planner":
                state.current_node = "researcher"
            elif node_name == "researcher":
                state.current_node = "executor"
            elif node_name == "executor":
                state.current_node = "reviewer"
            elif node_name == "reviewer":
                if state.metadata.get("review_passed"):
                    state.current_node = "approval_gate"
                elif state.revision_count <= state.max_revisions:
                    state.current_node = "executor"
                else:
                    state.current_node = "fallback"
            elif node_name == "approval_gate":
                state.current_node = "output"
            else:
                state.current_node = "fallback"

        self.store.save(state)
        return state
