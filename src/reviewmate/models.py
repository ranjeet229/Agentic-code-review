from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Finding(BaseModel):
    severity: Severity
    category: str = Field(min_length=1, max_length=80)
    file_path: str = Field(min_length=1)
    line_number: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=160)
    explanation: str = Field(min_length=1)
    suggested_fix: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)

    @field_validator("file_path")
    @classmethod
    def safe_path(cls, value: str) -> str:
        normalized = value.replace("\\", "/")
        while normalized.startswith("./"):
            normalized = normalized[2:]
        if not normalized or normalized.startswith("../") or "/../" in normalized:
            raise ValueError("file_path must be a repository-relative path")
        return normalized


class ReviewResponse(BaseModel):
    findings: list[Finding] = Field(default_factory=list)


class DiffChunk(BaseModel):
    file_path: str
    changed_lines: set[int]
    content: str
