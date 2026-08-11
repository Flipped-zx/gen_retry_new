from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ServiceError(Exception):
    status_code: int
    code: str
    message: str
    retryable: bool = False
    request_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def body(self) -> dict[str, Any]:
        error: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.request_id:
            error["request_id"] = self.request_id
        if self.details:
            error["details"] = self.details
        return {"error": error}


def safe_error_summary(exc: BaseException, limit: int = 500) -> str:
    text = " ".join(str(exc).replace("\x00", " ").split())
    if not text:
        text = type(exc).__name__
    return f"{type(exc).__name__}: {text}"[:limit]
