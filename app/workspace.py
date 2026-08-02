from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from threading import Lock


class FileOperation(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    RENAME = "rename"


class WorkspaceError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FileRecord:
    path: str
    content: str
    revision: int
    last_agent: str
    last_task_id: str
    reason: str


class Workspace:
    """Thread-safe virtual project workspace with path boundaries and ownership metadata."""

    _drive_pattern = re.compile(r"^[A-Za-z]:")

    def __init__(self) -> None:
        self._files: dict[str, FileRecord] = {}
        self._locks: dict[str, str] = {}
        self._lock = Lock()

    @classmethod
    def normalize_path(cls, raw_path: str) -> str:
        path = raw_path.strip().replace("\\", "/")
        if not path or path.startswith("/") or cls._drive_pattern.match(path):
            raise WorkspaceError("Path must be relative to the project workspace")
        candidate = PurePosixPath(path)
        if any(part in {"", ".", ".."} for part in candidate.parts):
            raise WorkspaceError("Unsafe workspace path")
        return candidate.as_posix()

    def acquire(self, path: str, task_id: str) -> None:
        safe_path = self.normalize_path(path)
        with self._lock:
            owner = self._locks.get(safe_path)
            if owner is not None and owner != task_id:
                raise WorkspaceError(f"File is locked by task {owner}")
            self._locks[safe_path] = task_id

    def release(self, path: str, task_id: str) -> None:
        safe_path = self.normalize_path(path)
        with self._lock:
            if self._locks.get(safe_path) == task_id:
                del self._locks[safe_path]

    def write(
        self,
        path: str,
        content: str,
        *,
        agent: str,
        task_id: str,
        reason: str,
        expected_revision: int | None = None,
    ) -> FileRecord:
        safe_path = self.normalize_path(path)
        if not agent.strip() or not task_id.strip() or not reason.strip():
            raise WorkspaceError("Agent, task ID and reason are required")
        with self._lock:
            owner = self._locks.get(safe_path)
            if owner is not None and owner != task_id:
                raise WorkspaceError(f"File is locked by task {owner}")
            current = self._files.get(safe_path)
            if expected_revision is not None:
                actual = current.revision if current else 0
                if actual != expected_revision:
                    raise WorkspaceError("File revision conflict")
            record = FileRecord(
                path=safe_path,
                content=content,
                revision=(current.revision + 1) if current else 1,
                last_agent=agent.strip(),
                last_task_id=task_id.strip(),
                reason=reason.strip(),
            )
            self._files[safe_path] = record
            return record

    def read(self, path: str) -> FileRecord:
        safe_path = self.normalize_path(path)
        with self._lock:
            record = self._files.get(safe_path)
            if record is None:
                raise WorkspaceError("File not found")
            return record

    def delete(self, path: str, *, task_id: str) -> None:
        safe_path = self.normalize_path(path)
        with self._lock:
            owner = self._locks.get(safe_path)
            if owner is not None and owner != task_id:
                raise WorkspaceError(f"File is locked by task {owner}")
            if safe_path not in self._files:
                raise WorkspaceError("File not found")
            del self._files[safe_path]

    def list_files(self) -> list[FileRecord]:
        with self._lock:
            return [self._files[path] for path in sorted(self._files)]
