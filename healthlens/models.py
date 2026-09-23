"""Validated, source-preserving domain models."""
from datetime import date as Date, datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


def uid() -> str:
    return uuid4().hex


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class Patient(BaseModel):
    id: str
    name: str
    initials: str
    age: int | None = None
    sex: str = "Not recorded"
    description: str = "Synthetic demonstration record"


class Observation(BaseModel):
    id: str = Field(default_factory=uid)
    patient_id: str
    document_id: str
    name: str
    category: str = "General"
    value: float = Field(allow_inf_nan=False)
    original_value: str
    comparator: Literal["=", "<", ">", "<=", ">="] = "="
    unit: str
    low: float | None = Field(default=None, allow_inf_nan=False)
    high: float | None = Field(default=None, allow_inf_nan=False)
    date: Date | None = None
    locator: str
    source_text: str
    status: Literal["needs_review", "accepted", "corrected", "rejected"] = "needs_review"
    version: int = 1
    specimen: str = "Not recorded"
    method: str = "Not recorded"

    @model_validator(mode="after")
    def range_order(self):
        if self.low is not None and self.high is not None and self.low > self.high:
            raise ValueError("Reference minimum must not exceed maximum.")
        return self


class Document(BaseModel):
    id: str = Field(default_factory=uid)
    patient_id: str
    name: str
    kind: str = "Laboratory report"
    source: str = "Local upload"
    date: Date | None = None
    hash: str
    pages: list[dict]
    status: str = "Needs review"
    created_at: str = Field(default_factory=timestamp)
    ocr: bool = False
    version: int = 1
    warnings: list[str] = Field(default_factory=list)


class Revision(BaseModel):
    observation_id: str
    actor: str = "Demo reviewer"
    at: str = Field(default_factory=timestamp)
    reason: str
    before: dict
    after: dict
