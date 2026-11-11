from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Column(StrictModel):
    name: str
    unit: str | None = None
    kind: Literal["number", "text"] = "number"
    rtol: float = Field(default=1e-6, ge=0, le=0.01)
    atol: float = Field(default=1e-8, ge=0, le=1)


class Question(StrictModel):
    id: str
    family: str
    title: str
    prompt: str
    difficulty: Literal["easy", "medium", "hard"]
    tags: list[str]
    decision: Literal["answer", "clarify", "abstain"] = "answer"
    columns: list[Column] = []
    ordered: bool = False
    query: str | None = None
    take: int | None = Field(default=None, ge=1, le=500)
    rationale: str
    caveat: str
    expert_review: Literal["pending", "approved"] = "pending"

    @model_validator(mode="after")
    def answer_needs_query(self):
        if self.decision == "answer" and (not self.query or not self.columns):
            raise ValueError("Answer tasks require a query and column contracts")
        if len({c.name for c in self.columns}) != len(self.columns):
            raise ValueError("Duplicate column names")
        return self


class Result(StrictModel):
    status: Literal["ok", "partial", "unavailable", "error"]
    rows: list[dict[str, JsonValue]] = Field(default_factory=list, max_length=10000)
    units: dict[str, str | None] = Field(default_factory=dict)
    error: str | None = None
    failure_origin: Literal["archive", "transport", "contract"] | None = None
    provenance: dict[str, JsonValue] = Field(default_factory=dict)


class Submission(StrictModel):
    question_id: str
    decision: Literal["answer", "clarify", "abstain"] = "answer"
    result: Result | None = None
    explanation: str = Field(default="", max_length=6000)


class Verdict(StrictModel):
    status: Literal["match", "mismatch", "inconclusive", "decision_match"]
    reason: str
    scope: str = "result agreement only; scientific reasoning is not scored"
