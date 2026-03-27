"""Structured operation results used by scripts and CI artifacts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class OperationResult:
    """Machine-readable result shape for pipeline and orchestration consumers."""

    status: str
    stage: str
    backend: str
    rule_id: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return a normalized dictionary payload for JSON artifacts."""
        return {
            "status": self.status,
            "stage": self.stage,
            "rule_id": self.rule_id,
            "backend": self.backend,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "artifacts": self.artifacts,
            "context": self.context,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }


def build_result(
    *,
    status: str,
    stage: str,
    backend: str,
    rule_id: Optional[str] = None,
    errors: Optional[List[str]] = None,
    warnings: Optional[List[str]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    artifacts: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience constructor for operation result dictionaries."""
    return OperationResult(
        status=status,
        stage=stage,
        backend=backend,
        rule_id=rule_id,
        errors=errors or [],
        warnings=warnings or [],
        metrics=metrics or {},
        artifacts=artifacts or {},
        context=context or {},
    ).to_dict()
