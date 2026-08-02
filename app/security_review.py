from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class SecurityFinding:
    rule_id: str
    severity: Severity
    path: str
    line: int
    message: str


@dataclass(frozen=True, slots=True)
class SecurityReport:
    findings: tuple[SecurityFinding, ...]

    @property
    def blocking(self) -> bool:
        return any(item.severity in {Severity.HIGH, Severity.CRITICAL} for item in self.findings)


class SecurityReviewer:
    """Deterministic first-pass scanner; complements, not replaces, human/agent review."""

    _rules: tuple[tuple[str, Severity, re.Pattern[str], str], ...] = (
        (
            "SEC001",
            Severity.CRITICAL,
            re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]"),
            "Possible hard-coded credential",
        ),
        (
            "SEC002",
            Severity.HIGH,
            re.compile(r"(?i)\b(?:eval|exec)\s*\("),
            "Dynamic code execution requires explicit security review",
        ),
        (
            "SEC003",
            Severity.HIGH,
            re.compile(r"(?i)subprocess\.(?:run|popen|call)\([^\n]*shell\s*=\s*True"),
            "Shell execution is enabled",
        ),
        (
            "SEC004",
            Severity.MEDIUM,
            re.compile(r"(?i)allow_origins\s*=\s*\[?['\"]\*['\"]\]?"),
            "Wildcard CORS origin detected",
        ),
        (
            "SEC005",
            Severity.HIGH,
            re.compile(r"(?i)dangerouslySetInnerHTML"),
            "Raw HTML rendering requires XSS review",
        ),
    )

    _ignored_parts = frozenset({"node_modules", ".git", "dist", "build", ".venv", "venv"})

    @classmethod
    def _eligible(cls, path: str) -> bool:
        parts = PurePosixPath(path.replace("\\", "/")).parts
        return not any(part in cls._ignored_parts for part in parts)

    def scan_file(self, path: str, content: str) -> tuple[SecurityFinding, ...]:
        if not self._eligible(path):
            return ()
        findings: list[SecurityFinding] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            for rule_id, severity, pattern, message in self._rules:
                if pattern.search(line):
                    findings.append(SecurityFinding(rule_id, severity, path, line_number, message))
        return tuple(findings)

    def scan_project(self, files: dict[str, str]) -> SecurityReport:
        findings: list[SecurityFinding] = []
        for path in sorted(files):
            findings.extend(self.scan_file(path, files[path]))
        return SecurityReport(tuple(findings))
