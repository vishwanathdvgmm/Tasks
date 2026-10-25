from __future__ import annotations

import json
from pathlib import Path
from .state import AgentState

class CheckpointStore:
    """Simple local JSON checkpoint store for assignment/demo use."""

    def __init__(self, directory: str | Path = ".task10_checkpoints") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(self, state: AgentState) -> Path:
        path = self.directory / f"{state.run_id}.json"
        temp = path.with_suffix(".tmp")
        temp.write_text(state.model_dump_json(indent=2), encoding="utf-8")
        temp.replace(path)
        return path

    def load(self, run_id: str) -> AgentState:
        # Prevent path traversal: only accept generated ID-like filenames.
        if not run_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in run_id):
            raise ValueError("Invalid run/approval ID")
        path = self.directory / f"{run_id}.json"
        if not path.is_file():
            raise FileNotFoundError(f"No checkpoint found for ID: {run_id}")
        return AgentState.model_validate(json.loads(path.read_text(encoding="utf-8")))
