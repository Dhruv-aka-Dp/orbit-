from datetime import date, datetime
from pydantic import BaseModel, Field


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    goal: str = Field(default="", max_length=5000)
    due_date: date | None = None


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    project_id: str | None = None
    priority: int = Field(default=2, ge=1, le=3)
    due_date: date | None = None
    estimate_hours: float | None = Field(default=None, ge=0, le=1000)
    dependency_id: str | None = None


class TaskPatch(BaseModel):
    status: str | None = None
    due_date: date | None = None
    project_id: str | None = None
    priority: int | None = Field(default=None, ge=1, le=3)


class MilestoneCreate(BaseModel):
    project_id: str
    title: str = Field(min_length=1, max_length=240)
    acceptance_criteria: str = Field(default="", max_length=5000)
    due_date: date | None = None


class MilestonePatch(BaseModel):
    due_date: date | None = None
    reason: str = Field(default="", max_length=1000)
    completion_evidence: str | None = Field(default=None, max_length=5000)


class MemberCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    role: str = Field(pattern="^(admin|member|viewer)$")


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(default="", max_length=50000)
    project_id: str | None = None


class CallRequest(BaseModel):
    mode: str = Field(default="on_demand", pattern="^(on_demand|scheduled|adaptive)$")


class CallPreferencePatch(BaseModel):
    phone: str | None = Field(default=None, max_length=32)
    timezone: str | None = Field(default=None, max_length=64)
    calls_consent: bool | None = None
    recording_consent: bool | None = None
    paused: bool | None = None
    allowed_from: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    allowed_to: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    daily_max: int | None = Field(default=None, ge=1, le=10)
    weekly_max: int | None = Field(default=None, ge=1, le=50)


class PlanDraftRequest(BaseModel):
    goal: str = Field(min_length=3, max_length=8000)
    capacity_hours: float | None = Field(default=None, ge=0, le=168)


class AuditOut(BaseModel):
    id: str
    action: str
    entity: str
    entity_id: str
    before: dict | None
    after: dict | None
    reason: str
    source: str
    correlation_id: str
    created_at: datetime

    class Config:
        from_attributes = True
