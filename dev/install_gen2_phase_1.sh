#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

if [[ ! -d ".git" ]]; then
    echo "ERROR: Run this from the JARVIS repository root or pass the repo path."
    exit 1
fi

mkdir -p \
    core/executive \
    tests \
    dev \
    docs/architecture

cat > core/executive/__init__.py <<'PY'
"""JARVIS Gen 2 executive orchestration package."""

from core.executive.director import ExecutiveDirector
from core.executive.engine import MissionEngine
from core.executive.models import (
    Mission,
    MissionStatus,
    MissionTask,
    TaskStatus,
)
from core.executive.planner import MissionPlanner
from core.executive.registry import DirectorRegistry
from core.executive.store import MissionStore

__all__ = [
    "DirectorRegistry",
    "ExecutiveDirector",
    "Mission",
    "MissionEngine",
    "MissionPlanner",
    "MissionStatus",
    "MissionStore",
    "MissionTask",
    "TaskStatus",
]
PY

cat > core/executive/models.py <<'PY'
"""Domain models for the JARVIS Gen 2 mission system."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


class MissionStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass(slots=True)
class MissionTask:
    """One executable unit within a mission plan."""

    title: str
    director: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    task_id: str = field(default_factory=lambda: uuid4().hex)
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MissionTask":
        values = dict(data)
        values["status"] = TaskStatus(values.get("status", TaskStatus.PENDING.value))
        return cls(**values)


@dataclass(slots=True)
class Mission:
    """Persistent mission managed by the Executive Director."""

    objective: str
    context: dict[str, Any] = field(default_factory=dict)
    mission_id: str = field(default_factory=lambda: uuid4().hex)
    status: MissionStatus = MissionStatus.DRAFT
    tasks: list[MissionTask] = field(default_factory=list)
    summary: dict[str, Any] | None = None
    error: str | None = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "context": self.context,
            "status": self.status.value,
            "tasks": [task.to_dict() for task in self.tasks],
            "summary": self.summary,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Mission":
        values = dict(data)
        values["status"] = MissionStatus(
            values.get("status", MissionStatus.DRAFT.value)
        )
        values["tasks"] = [
            MissionTask.from_dict(task) for task in values.get("tasks", [])
        ]
        return cls(**values)


@dataclass(slots=True)
class TaskExecutionResult:
    """Normalized response from a director handler."""

    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
PY

cat > core/executive/contracts.py <<'PY'
"""Protocols and exceptions for executive orchestration."""

from __future__ import annotations

from typing import Protocol

from core.executive.models import Mission, MissionTask, TaskExecutionResult


class DirectorHandler(Protocol):
    """Callable contract implemented by every task director."""

    def __call__(
        self,
        mission: Mission,
        task: MissionTask,
    ) -> TaskExecutionResult:
        ...


class ExecutiveError(RuntimeError):
    """Base exception for the Gen 2 executive layer."""


class DirectorNotRegisteredError(ExecutiveError):
    """Raised when a task references an unknown director."""


class MissionNotFoundError(ExecutiveError):
    """Raised when a mission cannot be found."""


class InvalidMissionPlanError(ExecutiveError):
    """Raised when mission dependencies are invalid or cyclic."""
PY

cat > core/executive/registry.py <<'PY'
"""Director registry used by the Mission Engine."""

from __future__ import annotations

from collections.abc import Iterable

from core.executive.contracts import DirectorHandler, DirectorNotRegisteredError


class DirectorRegistry:
    """Maps stable director names to executable handlers."""

    def __init__(self) -> None:
        self._handlers: dict[str, DirectorHandler] = {}

    def register(
        self,
        name: str,
        handler: DirectorHandler,
        *,
        replace: bool = False,
    ) -> None:
        normalized = self._normalize(name)
        if normalized in self._handlers and not replace:
            raise ValueError(f"Director already registered: {normalized}")
        self._handlers[normalized] = handler

    def unregister(self, name: str) -> None:
        self._handlers.pop(self._normalize(name), None)

    def resolve(self, name: str) -> DirectorHandler:
        normalized = self._normalize(name)
        try:
            return self._handlers[normalized]
        except KeyError as exc:
            raise DirectorNotRegisteredError(
                f"No director registered for '{normalized}'"
            ) from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def contains(self, name: str) -> bool:
        return self._normalize(name) in self._handlers

    def require(self, names: Iterable[str]) -> None:
        missing = [name for name in names if not self.contains(name)]
        if missing:
            raise DirectorNotRegisteredError(
                "Missing required directors: " + ", ".join(sorted(missing))
            )

    @staticmethod
    def _normalize(name: str) -> str:
        normalized = name.strip().lower().replace(" ", "_")
        if not normalized:
            raise ValueError("Director name cannot be empty")
        return normalized
PY

cat > core/executive/planner.py <<'PY'
"""Deterministic first-generation mission planner for JARVIS Gen 2."""

from __future__ import annotations

from dataclasses import dataclass

from core.executive.models import Mission, MissionStatus, MissionTask, utc_now


@dataclass(frozen=True, slots=True)
class PlanningRule:
    keywords: tuple[str, ...]
    director: str
    action: str
    title: str


DEFAULT_RULES: tuple[PlanningRule, ...] = (
    PlanningRule(
        keywords=(
            "knowledge",
            "research",
            "find",
            "search",
            "explain",
            "summarize",
            "document",
            "book",
            "catalog",
        ),
        director="knowledge",
        action="search",
        title="Gather relevant knowledge",
    ),
    PlanningRule(
        keywords=(
            "linux",
            "ubuntu",
            "windows",
            "macos",
            "kali",
            "system",
            "computer",
            "diagnose",
            "repair",
            "install",
        ),
        director="system",
        action="assess",
        title="Assess system requirements",
    ),
)


class MissionPlanner:
    """
    Produces deterministic, auditable plans.

    This planner intentionally avoids LLM dependence. A later Gen 2 phase can
    add an LLM planner behind the same interface without changing the engine.
    """

    def __init__(
        self,
        rules: tuple[PlanningRule, ...] = DEFAULT_RULES,
    ) -> None:
        self._rules = rules

    def plan(self, mission: Mission) -> Mission:
        if not mission.objective.strip():
            raise ValueError("Mission objective cannot be empty")

        analyze = MissionTask(
            title="Analyze mission objective",
            director="executive",
            action="analyze",
            payload={
                "objective": mission.objective,
                "context": mission.context,
            },
        )

        delegated_tasks: list[MissionTask] = []
        objective_text = mission.objective.casefold()

        for rule in self._rules:
            if any(keyword in objective_text for keyword in rule.keywords):
                delegated_tasks.append(
                    MissionTask(
                        title=rule.title,
                        director=rule.director,
                        action=rule.action,
                        payload={
                            "objective": mission.objective,
                            "context": mission.context,
                        },
                        depends_on=[analyze.task_id],
                    )
                )

        if not delegated_tasks:
            delegated_tasks.append(
                MissionTask(
                    title="Develop a general solution",
                    director="executive",
                    action="reason",
                    payload={
                        "objective": mission.objective,
                        "context": mission.context,
                    },
                    depends_on=[analyze.task_id],
                )
            )

        synthesize = MissionTask(
            title="Synthesize mission result",
            director="executive",
            action="synthesize",
            payload={"objective": mission.objective},
            depends_on=[task.task_id for task in delegated_tasks],
        )

        mission.tasks = [analyze, *delegated_tasks, synthesize]
        mission.status = MissionStatus.PLANNED
        mission.updated_at = utc_now()
        return mission
PY

cat > core/executive/store.py <<'PY'
"""SQLite persistence for JARVIS Gen 2 missions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any

from core.executive.contracts import MissionNotFoundError
from core.executive.models import Mission


class MissionStore:
    """Thread-safe SQLite repository storing complete mission snapshots."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS missions (
                    mission_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS mission_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (mission_id) REFERENCES missions(mission_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_missions_status
                ON missions(status)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_mission_id
                ON mission_events(mission_id)
                """
            )

    def save(self, mission: Mission) -> None:
        payload = json.dumps(
            mission.to_dict(),
            ensure_ascii=False,
            sort_keys=True,
        )
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO missions (
                    mission_id,
                    objective,
                    status,
                    payload_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(mission_id) DO UPDATE SET
                    objective = excluded.objective,
                    status = excluded.status,
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (
                    mission.mission_id,
                    mission.objective,
                    mission.status.value,
                    payload,
                    mission.created_at,
                    mission.updated_at,
                ),
            )

    def load(self, mission_id: str) -> Mission:
        with self._lock, self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM missions WHERE mission_id = ?",
                (mission_id,),
            ).fetchone()

        if row is None:
            raise MissionNotFoundError(f"Mission not found: {mission_id}")

        data = json.loads(row["payload_json"])
        return Mission.from_dict(data)

    def list(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mission]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        query = "SELECT payload_json FROM missions"
        parameters: list[Any] = []
        if status:
            query += " WHERE status = ?"
            parameters.append(status)
        query += " ORDER BY updated_at DESC LIMIT ?"
        parameters.append(limit)

        with self._lock, self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()

        return [
            Mission.from_dict(json.loads(row["payload_json"]))
            for row in rows
        ]

    def record_event(
        self,
        mission_id: str,
        event_type: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO mission_events (
                    mission_id,
                    event_type,
                    payload_json,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    mission_id,
                    event_type,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    created_at,
                ),
            )

    def events(self, mission_id: str) -> list[dict[str, Any]]:
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_type, payload_json, created_at
                FROM mission_events
                WHERE mission_id = ?
                ORDER BY event_id ASC
                """,
                (mission_id,),
            ).fetchall()

        return [
            {
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]
PY

cat > core/executive/handlers.py <<'PY'
"""Built-in director handlers for the Gen 2 executive foundation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from core.executive.models import Mission, MissionTask, TaskExecutionResult


def executive_handler(
    mission: Mission,
    task: MissionTask,
) -> TaskExecutionResult:
    """Handle core analysis, reasoning, and synthesis actions."""
    if task.action == "analyze":
        return TaskExecutionResult(
            success=True,
            output={
                "objective": mission.objective,
                "context_keys": sorted(mission.context),
                "objective_length": len(mission.objective),
                "assessment": "Mission objective accepted and normalized.",
            },
        )

    if task.action == "reason":
        return TaskExecutionResult(
            success=True,
            output={
                "approach": (
                    "General executive reasoning path selected because no "
                    "specialist planning rule matched the objective."
                ),
                "objective": mission.objective,
            },
        )

    if task.action == "synthesize":
        completed_outputs = [
            {
                "task_id": candidate.task_id,
                "title": candidate.title,
                "director": candidate.director,
                "output": candidate.result,
            }
            for candidate in mission.tasks
            if candidate.task_id != task.task_id and candidate.result is not None
        ]
        return TaskExecutionResult(
            success=True,
            output={
                "objective": mission.objective,
                "completed_task_count": len(completed_outputs),
                "task_outputs": completed_outputs,
            },
        )

    return TaskExecutionResult(
        success=False,
        error=f"Unsupported executive action: {task.action}",
    )


def placeholder_system_handler(
    mission: Mission,
    task: MissionTask,
) -> TaskExecutionResult:
    """
    Safe Phase I system adapter.

    It prepares delegation data but performs no host changes. A later phase
    will connect this contract to OS-specific specialists and guarded tools.
    """
    return TaskExecutionResult(
        success=True,
        output={
            "mode": "assessment_only",
            "objective": mission.objective,
            "requested_action": task.action,
            "message": (
                "System task accepted. Active OS execution is intentionally "
                "disabled in Gen 2 Phase I."
            ),
        },
    )


KnowledgeSearch = Callable[[str, dict[str, Any]], dict[str, Any]]


class KnowledgeHandler:
    """
    Bridge contract for the existing Knowledge Director.

    Pass a callable with signature:
        search(objective: str, context: dict) -> dict

    Until connected, the handler remains safe and explicit rather than
    guessing the current Knowledge Director API.
    """

    def __init__(self, search: KnowledgeSearch | None = None) -> None:
        self._search = search

    def __call__(
        self,
        mission: Mission,
        task: MissionTask,
    ) -> TaskExecutionResult:
        if self._search is None:
            return TaskExecutionResult(
                success=True,
                output={
                    "mode": "bridge_ready",
                    "objective": mission.objective,
                    "requested_action": task.action,
                    "message": (
                        "Knowledge task routed successfully. Connect the "
                        "existing Knowledge Director through KnowledgeHandler."
                    ),
                },
            )

        try:
            output = self._search(mission.objective, mission.context)
        except Exception as exc:  # boundary: external director integration
            return TaskExecutionResult(
                success=False,
                error=f"Knowledge Director failed: {exc}",
            )

        if not isinstance(output, dict):
            output = {"result": output}

        return TaskExecutionResult(success=True, output=output)
PY

cat > core/executive/engine.py <<'PY'
"""Dependency-aware execution engine for JARVIS missions."""

from __future__ import annotations

from core.executive.contracts import InvalidMissionPlanError
from core.executive.models import (
    Mission,
    MissionStatus,
    MissionTask,
    TaskStatus,
    utc_now,
)
from core.executive.registry import DirectorRegistry
from core.executive.store import MissionStore


class MissionEngine:
    """Executes mission tasks and persists every state transition."""

    def __init__(
        self,
        registry: DirectorRegistry,
        store: MissionStore,
    ) -> None:
        self.registry = registry
        self.store = store

    def execute(self, mission: Mission) -> Mission:
        self._validate_plan(mission)

        mission.status = MissionStatus.RUNNING
        mission.started_at = mission.started_at or utc_now()
        mission.updated_at = utc_now()
        self._persist(mission, "mission_started", {})

        while True:
            pending = [
                task
                for task in mission.tasks
                if task.status in {TaskStatus.PENDING, TaskStatus.READY}
            ]
            if not pending:
                break

            progress = False
            for task in pending:
                dependency_states = self._dependency_states(mission, task)

                if any(
                    state in {TaskStatus.FAILED, TaskStatus.BLOCKED}
                    for state in dependency_states
                ):
                    task.status = TaskStatus.BLOCKED
                    task.error = "One or more dependencies failed or were blocked."
                    task.completed_at = utc_now()
                    mission.updated_at = utc_now()
                    self._persist(
                        mission,
                        "task_blocked",
                        {"task_id": task.task_id, "error": task.error},
                    )
                    progress = True
                    continue

                if not all(
                    state == TaskStatus.COMPLETED
                    for state in dependency_states
                ):
                    continue

                task.status = TaskStatus.READY
                self._run_task(mission, task)
                progress = True

            if not progress:
                mission.status = MissionStatus.BLOCKED
                mission.error = (
                    "Mission made no progress. Check for unresolved or cyclic "
                    "task dependencies."
                )
                mission.updated_at = utc_now()
                self._persist(
                    mission,
                    "mission_blocked",
                    {"error": mission.error},
                )
                return mission

        failed_tasks = [
            task for task in mission.tasks if task.status == TaskStatus.FAILED
        ]
        blocked_tasks = [
            task for task in mission.tasks if task.status == TaskStatus.BLOCKED
        ]

        if failed_tasks:
            mission.status = MissionStatus.FAILED
            mission.error = f"{len(failed_tasks)} task(s) failed."
        elif blocked_tasks:
            mission.status = MissionStatus.BLOCKED
            mission.error = f"{len(blocked_tasks)} task(s) were blocked."
        else:
            mission.status = MissionStatus.COMPLETED
            mission.summary = self._mission_summary(mission)
            mission.completed_at = utc_now()

        mission.updated_at = utc_now()
        self._persist(
            mission,
            f"mission_{mission.status.value}",
            {
                "summary": mission.summary,
                "error": mission.error,
            },
        )
        return mission

    def _run_task(self, mission: Mission, task: MissionTask) -> None:
        task.status = TaskStatus.RUNNING
        task.started_at = utc_now()
        mission.updated_at = utc_now()
        self._persist(
            mission,
            "task_started",
            {
                "task_id": task.task_id,
                "director": task.director,
                "action": task.action,
            },
        )

        try:
            handler = self.registry.resolve(task.director)
            execution = handler(mission, task)
        except Exception as exc:  # engine boundary
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.completed_at = utc_now()
            mission.updated_at = utc_now()
            self._persist(
                mission,
                "task_failed",
                {"task_id": task.task_id, "error": task.error},
            )
            return

        task.completed_at = utc_now()
        mission.updated_at = utc_now()

        if execution.success:
            task.status = TaskStatus.COMPLETED
            task.result = execution.output
            task.error = None
            self._persist(
                mission,
                "task_completed",
                {"task_id": task.task_id, "result": task.result},
            )
        else:
            task.status = TaskStatus.FAILED
            task.error = execution.error or "Director returned failure."
            self._persist(
                mission,
                "task_failed",
                {"task_id": task.task_id, "error": task.error},
            )

    def _dependency_states(
        self,
        mission: Mission,
        task: MissionTask,
    ) -> list[TaskStatus]:
        by_id = {candidate.task_id: candidate for candidate in mission.tasks}
        return [by_id[task_id].status for task_id in task.depends_on]

    def _validate_plan(self, mission: Mission) -> None:
        if not mission.tasks:
            raise InvalidMissionPlanError("Mission has no tasks")

        task_ids = [task.task_id for task in mission.tasks]
        if len(task_ids) != len(set(task_ids)):
            raise InvalidMissionPlanError("Mission contains duplicate task IDs")

        known = set(task_ids)
        for task in mission.tasks:
            missing = set(task.depends_on) - known
            if missing:
                raise InvalidMissionPlanError(
                    f"Task {task.task_id} has missing dependencies: "
                    + ", ".join(sorted(missing))
                )
            if task.task_id in task.depends_on:
                raise InvalidMissionPlanError(
                    f"Task {task.task_id} depends on itself"
                )

        visiting: set[str] = set()
        visited: set[str] = set()
        dependencies = {
            task.task_id: tuple(task.depends_on) for task in mission.tasks
        }

        def visit(task_id: str) -> None:
            if task_id in visiting:
                raise InvalidMissionPlanError(
                    "Mission plan contains a dependency cycle"
                )
            if task_id in visited:
                return
            visiting.add(task_id)
            for dependency_id in dependencies[task_id]:
                visit(dependency_id)
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in task_ids:
            visit(task_id)

        self.registry.require(task.director for task in mission.tasks)

    def _persist(
        self,
        mission: Mission,
        event_type: str,
        payload: dict,
    ) -> None:
        self.store.save(mission)
        self.store.record_event(
            mission.mission_id,
            event_type,
            payload,
            utc_now(),
        )

    @staticmethod
    def _mission_summary(mission: Mission) -> dict:
        return {
            "objective": mission.objective,
            "status": mission.status.value,
            "task_count": len(mission.tasks),
            "completed_tasks": sum(
                task.status == TaskStatus.COMPLETED for task in mission.tasks
            ),
            "directors_used": sorted(
                {task.director for task in mission.tasks}
            ),
        }
PY

cat > core/executive/director.py <<'PY'
"""Top-level Executive Director facade for JARVIS Gen 2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.executive.engine import MissionEngine
from core.executive.handlers import (
    KnowledgeHandler,
    KnowledgeSearch,
    executive_handler,
    placeholder_system_handler,
)
from core.executive.models import Mission, MissionStatus, utc_now
from core.executive.planner import MissionPlanner
from core.executive.registry import DirectorRegistry
from core.executive.store import MissionStore


class ExecutiveDirector:
    """Creates, plans, executes, resumes, and inspects missions."""

    def __init__(
        self,
        *,
        database_path: str | Path,
        registry: DirectorRegistry | None = None,
        planner: MissionPlanner | None = None,
        knowledge_search: KnowledgeSearch | None = None,
    ) -> None:
        self.registry = registry or DirectorRegistry()
        self.planner = planner or MissionPlanner()
        self.store = MissionStore(database_path)

        if not self.registry.contains("executive"):
            self.registry.register("executive", executive_handler)
        if not self.registry.contains("knowledge"):
            self.registry.register(
                "knowledge",
                KnowledgeHandler(search=knowledge_search),
            )
        if not self.registry.contains("system"):
            self.registry.register("system", placeholder_system_handler)

        self.engine = MissionEngine(self.registry, self.store)

    def create_mission(
        self,
        objective: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> Mission:
        mission = Mission(
            objective=objective.strip(),
            context=context or {},
        )
        if not mission.objective:
            raise ValueError("Mission objective cannot be empty")
        self.store.save(mission)
        self.store.record_event(
            mission.mission_id,
            "mission_created",
            {"objective": mission.objective},
            utc_now(),
        )
        return mission

    def plan_mission(self, mission: Mission) -> Mission:
        planned = self.planner.plan(mission)
        self.store.save(planned)
        self.store.record_event(
            planned.mission_id,
            "mission_planned",
            {
                "task_count": len(planned.tasks),
                "directors": sorted(
                    {task.director for task in planned.tasks}
                ),
            },
            utc_now(),
        )
        return planned

    def submit(
        self,
        objective: str,
        *,
        context: dict[str, Any] | None = None,
        execute: bool = True,
    ) -> Mission:
        mission = self.create_mission(objective, context=context)
        mission = self.plan_mission(mission)
        if execute:
            mission = self.engine.execute(mission)
        return mission

    def execute_mission(self, mission_id: str) -> Mission:
        mission = self.store.load(mission_id)
        if mission.status == MissionStatus.DRAFT:
            mission = self.plan_mission(mission)
        if mission.status in {
            MissionStatus.COMPLETED,
            MissionStatus.CANCELLED,
        }:
            return mission
        return self.engine.execute(mission)

    def get_mission(self, mission_id: str) -> Mission:
        return self.store.load(mission_id)

    def list_missions(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> list[Mission]:
        return self.store.list(status=status, limit=limit)

    def mission_events(self, mission_id: str) -> list[dict[str, Any]]:
        self.store.load(mission_id)
        return self.store.events(mission_id)
PY

cat > core/executive/cli.py <<'PY'
"""Command-line interface for JARVIS Gen 2 missions."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from core.executive.director import ExecutiveDirector


def default_database_path() -> Path:
    configured = os.getenv("JARVIS_MISSION_DB")
    if configured:
        return Path(configured).expanduser()
    return Path("runtime/missions/jarvis_missions.sqlite3")


def parse_context(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("--context must decode to a JSON object")
    return data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jarvis-gen2",
        description="JARVIS Gen 2 Executive Director and Mission Engine",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=default_database_path(),
        help="Mission SQLite database path",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    submit = commands.add_parser("submit", help="Create and run a mission")
    submit.add_argument("objective")
    submit.add_argument(
        "--context",
        help="JSON object containing mission context",
    )
    submit.add_argument(
        "--plan-only",
        action="store_true",
        help="Create the plan without executing it",
    )

    show = commands.add_parser("show", help="Show one mission")
    show.add_argument("mission_id")
    show.add_argument(
        "--events",
        action="store_true",
        help="Include lifecycle events",
    )

    list_command = commands.add_parser("list", help="List missions")
    list_command.add_argument("--status")
    list_command.add_argument("--limit", type=int, default=20)

    execute = commands.add_parser(
        "execute",
        help="Execute a previously planned mission",
    )
    execute.add_argument("mission_id")

    return parser


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    director = ExecutiveDirector(database_path=args.db)

    if args.command == "submit":
        mission = director.submit(
            args.objective,
            context=parse_context(args.context),
            execute=not args.plan_only,
        )
        print_json(mission.to_dict())
        return 0

    if args.command == "show":
        mission = director.get_mission(args.mission_id)
        data = mission.to_dict()
        if args.events:
            data["events"] = director.mission_events(args.mission_id)
        print_json(data)
        return 0

    if args.command == "list":
        missions = director.list_missions(
            status=args.status,
            limit=args.limit,
        )
        print_json([mission.to_dict() for mission in missions])
        return 0

    if args.command == "execute":
        mission = director.execute_mission(args.mission_id)
        print_json(mission.to_dict())
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
PY

cat > tests/test_gen2_executive.py <<'PY'
"""Tests for JARVIS Gen 2 Phase I."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.executive.contracts import InvalidMissionPlanError
from core.executive.director import ExecutiveDirector
from core.executive.engine import MissionEngine
from core.executive.models import (
    Mission,
    MissionStatus,
    MissionTask,
    TaskExecutionResult,
    TaskStatus,
)
from core.executive.registry import DirectorRegistry
from core.executive.store import MissionStore


class ExecutiveDirectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "missions.sqlite3"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_general_mission_completes(self) -> None:
        director = ExecutiveDirector(database_path=self.database)

        mission = director.submit("Draft a project execution strategy")

        self.assertEqual(mission.status, MissionStatus.COMPLETED)
        self.assertEqual(len(mission.tasks), 3)
        self.assertTrue(
            all(task.status == TaskStatus.COMPLETED for task in mission.tasks)
        )
        self.assertIsNotNone(mission.summary)

    def test_knowledge_mission_routes_to_knowledge_director(self) -> None:
        calls: list[tuple[str, dict]] = []

        def fake_search(objective: str, context: dict) -> dict:
            calls.append((objective, context))
            return {"matches": 3, "source": "fake-knowledge-director"}

        director = ExecutiveDirector(
            database_path=self.database,
            knowledge_search=fake_search,
        )

        mission = director.submit(
            "Search the knowledge catalog for Linux networking",
            context={"limit": 3},
        )

        self.assertEqual(mission.status, MissionStatus.COMPLETED)
        self.assertEqual(len(calls), 1)
        knowledge_tasks = [
            task for task in mission.tasks if task.director == "knowledge"
        ]
        self.assertEqual(len(knowledge_tasks), 1)
        self.assertEqual(
            knowledge_tasks[0].result,
            {"matches": 3, "source": "fake-knowledge-director"},
        )

    def test_mission_persists_and_reloads(self) -> None:
        director = ExecutiveDirector(database_path=self.database)
        mission = director.submit("Explain the current knowledge architecture")

        reloaded = director.get_mission(mission.mission_id)

        self.assertEqual(reloaded.mission_id, mission.mission_id)
        self.assertEqual(reloaded.status, MissionStatus.COMPLETED)
        self.assertEqual(len(reloaded.tasks), len(mission.tasks))
        self.assertGreaterEqual(
            len(director.mission_events(mission.mission_id)),
            4,
        )

    def test_failed_director_blocks_dependent_synthesis(self) -> None:
        registry = DirectorRegistry()

        def good_handler(
            mission: Mission,
            task: MissionTask,
        ) -> TaskExecutionResult:
            return TaskExecutionResult(success=True, output={"ok": True})

        def bad_handler(
            mission: Mission,
            task: MissionTask,
        ) -> TaskExecutionResult:
            return TaskExecutionResult(success=False, error="controlled failure")

        registry.register("executive", good_handler)
        registry.register("failure", bad_handler)

        store = MissionStore(self.database)
        engine = MissionEngine(registry, store)

        first = MissionTask(
            title="Fail",
            director="failure",
            action="fail",
        )
        second = MissionTask(
            title="Blocked",
            director="executive",
            action="synthesize",
            depends_on=[first.task_id],
        )
        mission = Mission(
            objective="Test controlled failure",
            status=MissionStatus.PLANNED,
            tasks=[first, second],
        )
        store.save(mission)

        result = engine.execute(mission)

        self.assertEqual(result.status, MissionStatus.FAILED)
        self.assertEqual(first.status, TaskStatus.FAILED)
        self.assertEqual(second.status, TaskStatus.BLOCKED)

    def test_cycle_is_rejected(self) -> None:
        registry = DirectorRegistry()
        registry.register(
            "executive",
            lambda mission, task: TaskExecutionResult(success=True),
        )
        store = MissionStore(self.database)
        engine = MissionEngine(registry, store)

        first = MissionTask(
            title="First",
            director="executive",
            action="one",
        )
        second = MissionTask(
            title="Second",
            director="executive",
            action="two",
        )
        first.depends_on = [second.task_id]
        second.depends_on = [first.task_id]

        mission = Mission(
            objective="Cycle test",
            status=MissionStatus.PLANNED,
            tasks=[first, second],
        )

        with self.assertRaises(InvalidMissionPlanError):
            engine.execute(mission)


if __name__ == "__main__":
    unittest.main()
PY

cat > dev/verify_gen2_phase_1.sh <<'SH'
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "======================================================================"
echo "JARVIS GEN 2 PHASE I VERIFICATION"
echo "======================================================================"

echo
echo "[1/6] Python version"
"$PYTHON_BIN" --version

echo
echo "[2/6] Compile executive package"
"$PYTHON_BIN" -m compileall -q core/executive

echo
echo "[3/6] Import surface"
"$PYTHON_BIN" - <<'PY'
from core.executive import (
    DirectorRegistry,
    ExecutiveDirector,
    MissionEngine,
    MissionPlanner,
    MissionStore,
)

print("Executive imports: PASS")
PY

echo
echo "[4/6] Unit tests"
"$PYTHON_BIN" -m unittest -v tests.test_gen2_executive

echo
echo "[5/6] CLI smoke test"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

"$PYTHON_BIN" -m core.executive.cli \
    --db "$TMP_DIR/missions.sqlite3" \
    submit \
    "Search the knowledge catalog for the JARVIS architecture" \
    > "$TMP_DIR/result.json"

"$PYTHON_BIN" - "$TMP_DIR/result.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
data = json.loads(path.read_text(encoding="utf-8"))

assert data["status"] == "completed", data
assert len(data["tasks"]) >= 3, data
assert any(task["director"] == "knowledge" for task in data["tasks"]), data

print("CLI smoke test: PASS")
print(f"Mission ID: {data['mission_id']}")
print(f"Tasks     : {len(data['tasks'])}")
print(f"Status    : {data['status']}")
PY

echo
echo "[6/6] Working tree summary"
git status --short

echo
echo "======================================================================"
echo "GEN 2 PHASE I: PASS"
echo "Executive Director + Mission Engine are operational."
echo "======================================================================"
SH
chmod +x dev/verify_gen2_phase_1.sh

cat > docs/architecture/gen2_mission_engine.md <<'MD'
# JARVIS Gen 2 Phase I — Executive Director and Mission Engine

## Status

Implemented as the first additive milestone of JARVIS Generation 2.

## Purpose

Generation 1 established the Knowledge Engine, Knowledge Director,
explainable ranking, integrity checks, self-healing, runtime discovery, and
the Doctor framework.

Generation 2 introduces a supervisory intelligence layer. The first milestone
provides the contracts and lifecycle required for JARVIS to convert an
objective into a persistent mission, divide it into tasks, route each task to
a director, execute dependencies in order, audit state transitions, and
synthesize results.

## Architecture

```text
User Objective
      |
      v
ExecutiveDirector
      |
      +-- MissionPlanner
      |       |
      |       +-- deterministic task graph
      |
      +-- MissionEngine
      |       |
      |       +-- DirectorRegistry
      |       |       +-- executive
      |       |       +-- knowledge
      |       |       +-- system
      |       |
      |       +-- dependency execution
      |       +-- failure propagation
      |       +-- synthesis
      |
      +-- MissionStore
              +-- mission snapshots
              +-- lifecycle events
```

## Design decisions

### Additive architecture

Gen 2 does not replace the Knowledge Engine. It sits above it and delegates to
it through a stable bridge contract.

### Deterministic first planner

The first planner is deterministic and auditable. It uses explicit routing
rules rather than an LLM. A later planner may use a language model behind the
same `MissionPlanner` interface.

### Persistent missions

Missions are stored in SQLite. Every significant lifecycle transition is also
written to the `mission_events` table.

### Director isolation

The engine depends only on the `DirectorHandler` protocol. Directors may later
be local Python services, subprocesses, remote services, OS specialists, or
autonomous agents.

### Safe system behavior

The Phase I system director is assessment-only. It cannot modify the host.
Guarded execution, approval policies, and rollback belong to a later phase.

## Mission lifecycle

```text
draft
  -> planned
  -> running
  -> completed

running
  -> failed
  -> blocked

draft/planned/running
  -> cancelled
```

## Phase I completion criteria

- Mission domain models compile.
- SQLite persistence initializes automatically.
- Mission plans reject missing or cyclic dependencies.
- Tasks execute only after dependencies complete.
- Director failures are captured and propagated.
- Mission and task events are auditable.
- Knowledge tasks route through a bridge contract.
- System tasks remain non-destructive.
- CLI submission and inspection work.
- Unit and smoke tests pass.

## Next phase

Gen 2 Phase II should connect the existing Knowledge Director to
`KnowledgeHandler`, add capability declarations, and let the Executive
Director select among real registered directors based on capabilities rather
than keyword rules alone.
MD

echo
echo "Installed JARVIS Gen 2 Phase I files in:"
echo "  $ROOT"
echo
echo "Next command:"
echo "  ./dev/verify_gen2_phase_1.sh"
