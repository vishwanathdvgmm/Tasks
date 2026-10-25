from task10_agent_workflows.checkpoint import CheckpointStore
from task10_agent_workflows.graph import StateGraph

def test_workflow_completes(tmp_path):
    graph = StateGraph(CheckpointStore(tmp_path))
    state = graph.run("Research state graphs and calculate 12 * 7")
    assert state.status == "completed"
    assert any("84" in item for item in state.tool_results)
    assert "reviewer" in state.visited_nodes
    assert state.final_output

def test_reflection_retries_then_passes(tmp_path):
    graph = StateGraph(CheckpointStore(tmp_path))
    state = graph.run("Explain state graphs [force-review-retry]")
    assert state.status == "completed"
    assert state.revision_count == 1
    assert state.visited_nodes.count("executor") == 2

def test_human_approval_pause_resume(tmp_path):
    graph = StateGraph(CheckpointStore(tmp_path))
    paused = graph.run("Prepare a simulated destructive action", require_approval=True)
    assert paused.status == "paused"
    assert paused.approval_id == paused.run_id

    resumed = graph.resume(paused.approval_id, "approve")
    assert resumed.status == "completed"
    assert "Human approval: approved" in resumed.final_output

def test_human_rejection(tmp_path):
    graph = StateGraph(CheckpointStore(tmp_path))
    paused = graph.run("Send a simulated email", require_approval=True)
    rejected = graph.resume(paused.approval_id, "reject")
    assert rejected.status == "rejected"
    assert "No external action" in rejected.final_output

def test_step_limit_fallback(tmp_path):
    graph = StateGraph(CheckpointStore(tmp_path))
    state = graph.run("Any request", max_steps=1)
    assert state.status == "failed"
    assert "stopped safely" in state.final_output
