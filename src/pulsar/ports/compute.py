"""Where work runs. Research may leave the laptop; live orders may not."""

from __future__ import annotations

from typing import Any, Callable, Literal, Protocol, runtime_checkable

from pydantic import BaseModel

TaskKind = Literal["research", "validate", "sentry", "execute"]


class TaskRequest(BaseModel):
    kind: TaskKind
    payload: dict[str, Any] = {}
    allow_remote: bool = True


class TaskResult(BaseModel):
    kind: TaskKind
    where: Literal["local", "grokbot"]
    ok: bool
    detail: dict[str, Any] = {}


@runtime_checkable
class ComputePort(Protocol):
    name: str

    def submit(self, task: TaskRequest, fn: Callable[[], dict[str, Any]]) -> TaskResult: ...


class LocalCompute:
    name = "local"

    def submit(self, task: TaskRequest, fn: Callable[[], dict[str, Any]]) -> TaskResult:
        if task.kind == "execute" and task.allow_remote:
            # Live/paper fills always run where this process is. Remote is a no-op flag.
            pass
        try:
            detail = fn()
            return TaskResult(kind=task.kind, where="local", ok=True, detail=detail)
        except Exception as exc:  # noqa: BLE001 — surface worker errors to the caller
            return TaskResult(
                kind=task.kind, where="local", ok=False, detail={"error": str(exc)}
            )


def assert_execution_is_local(compute_name: str, task: TaskRequest) -> None:
    if task.kind == "execute" and compute_name != "local":
        raise PermissionError("execution tasks cannot run on Grok Bot or any remote compute")
