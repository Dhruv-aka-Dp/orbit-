"""Orbit's API: secure workspace-scoped productivity records and simulated call orchestration.

Real PSTN, recording and voice AI are deliberately not wired until a provider contract,
numbering route, retention policy and explicit release approval exist.
"""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Annotated
import jwt
from jwt import PyJWKClient
from fastapi import Depends, FastAPI, Header, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .ai import draft_plan
from .database import Base, engine, session
from .models import AuditEvent, Call, CallPreference, Membership, Milestone, Note, Project, Task, User, Workspace
from .schemas import CallPreferencePatch, CallRequest, MemberCreate, MilestoneCreate, MilestonePatch, NoteCreate, PlanDraftRequest, ProjectCreate, TaskCreate, TaskPatch, WorkspaceCreate

settings = get_settings()
app = FastAPI(title="Orbit API", version="1.0.0", docs_url="/docs" if not settings.production else None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Orbit-Workspace", "X-Orbit-Dev-User"],
)

VALID_STATUSES = {"Inbox", "Todo", "In Progress", "Blocked", "Done", "Cancelled"}
WRITERS = {"owner", "admin", "member"}


def db_session() -> Session:
    yield from session()


def authenticated_user(
    authorization: Annotated[str | None, Header()] = None,
    x_orbit_dev_user: Annotated[str | None, Header()] = None,
    db: Session = Depends(db_session),
) -> User:
    claims: dict
    if authorization and authorization.startswith("Bearer "):
        if not settings.oidc_issuer or not settings.oidc_audience:
            raise HTTPException(503, "OIDC is not configured")
        token = authorization.removeprefix("Bearer ")
        try:
            jwks = PyJWKClient(settings.oidc_issuer.rstrip("/") + "/.well-known/jwks.json")
            key = jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, key.key, algorithms=[key.algorithm_name], audience=settings.oidc_audience, issuer=settings.oidc_issuer)
        except Exception as error:
            raise HTTPException(status_code=401, detail="Invalid identity token") from error
        user_id, email = str(claims["sub"]), claims.get("email")
    elif settings.allow_dev_auth and x_orbit_dev_user:
        user_id, email = x_orbit_dev_user.strip(), None
        if not user_id or len(user_id) > 64:
            raise HTTPException(401, "Invalid development user")
    else:
        raise HTTPException(401, "Authentication required")

    user = db.get(User, user_id)
    if not user:
        user = User(id=user_id, email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def workspace_member(
    user: User = Depends(authenticated_user),
    workspace_id: Annotated[str, Header(alias="X-Orbit-Workspace")] = "",
    db: Session = Depends(db_session),
) -> tuple[User, Membership, Session]:
    membership = db.scalar(select(Membership).where(Membership.workspace_id == workspace_id, Membership.user_id == user.id))
    if not membership:
        raise HTTPException(403, "No access to this workspace")
    return user, membership, db


def write_access(context: tuple[User, Membership, Session] = Depends(workspace_member)) -> tuple[User, Membership, Session]:
    if context[1].role not in WRITERS:
        raise HTTPException(403, "Your role is view-only")
    return context


def audit(db: Session, workspace_id: str, actor_id: str, action: str, entity: str, entity_id: str, before=None, after=None, reason="", source="dashboard") -> None:
    db.add(AuditEvent(workspace_id=workspace_id, actor_id=actor_id, action=action, entity=entity, entity_id=entity_id, before=before, after=after, reason=reason, source=source))


def one(db: Session, model, record_id: str, workspace_id: str):
    record = db.scalar(select(model).where(model.id == record_id, model.workspace_id == workspace_id))
    if not record:
        raise HTTPException(404, "Record not found")
    return record


def pref_for(db: Session, workspace_id: str, user_id: str) -> CallPreference:
    preference = db.scalar(select(CallPreference).where(CallPreference.workspace_id == workspace_id, CallPreference.user_id == user_id))
    if preference is None:
        preference = CallPreference(workspace_id=workspace_id, user_id=user_id)
        db.add(preference)
        db.flush()
    return preference


def call_policy(db: Session, workspace_id: str, user_id: str, preference: CallPreference) -> list[str]:
    reasons: list[str] = []
    try:
        local_now = datetime.now(ZoneInfo(preference.timezone))
    except ZoneInfoNotFoundError:
        reasons.append("Invalid user timezone")
        local_now = datetime.now(timezone.utc)
    if not preference.phone:
        reasons.append("No verified phone number")
    if not preference.calls_consent:
        reasons.append("AI-call consent is not granted")
    if preference.paused:
        reasons.append("All calls are paused")
    current = local_now.strftime("%H:%M")
    if not (preference.allowed_from <= current <= preference.allowed_to):
        reasons.append("Outside the allowed call window")
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    calls = db.scalars(select(Call).where(Call.workspace_id == workspace_id, Call.created_at >= seven_days_ago)).all()
    local_today = local_now.date()
    daily = sum(1 for call in calls if call.created_at.astimezone(local_now.tzinfo).date() == local_today)
    if daily >= preference.daily_max:
        reasons.append("Daily call limit reached")
    if len(calls) >= preference.weekly_max:
        reasons.append("Weekly call limit reached")
    return reasons


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store" if request.url.path.startswith(("/tasks", "/projects", "/notes", "/calls", "/audit", "/report")) else "public, max-age=60"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/healthz")
def healthz():
    return {"status": "ok", "environment": settings.env}


@app.post("/ai/plan-drafts")
async def create_plan_draft(payload: PlanDraftRequest, context=Depends(write_access)):
    """Generate a non-mutating AI draft. The user must explicitly create any records."""
    user, member, db = context
    try:
        text, response_id = await draft_plan(payload.goal, payload.capacity_hours)
    except RuntimeError as error:
        raise HTTPException(503, str(error)) from error
    except Exception as error:
        raise HTTPException(502, "AI provider request failed") from error
    audit(db, member.workspace_id, user.id, "ai.plan_drafted", "plan_draft", response_id, after={"model": settings.openai_model}, source="ai")
    db.commit()
    return {"draft": text, "provider_response_id": response_id, "model": settings.openai_model}


@app.get("/auth/config")
def auth_config():
    """Public OIDC metadata used by the browser's PKCE client; no secret is exposed."""
    return {
        "development": settings.allow_dev_auth,
        "issuer": settings.oidc_issuer,
        "audience": settings.oidc_audience,
        "client_id": settings.oidc_client_id,
        "redirect_uri": settings.oidc_redirect_uri,
    }


@app.get("/workspaces")
def list_workspaces(user: User = Depends(authenticated_user), db: Session = Depends(db_session)):
    rows = db.execute(select(Workspace, Membership.role).join(Membership, Membership.workspace_id == Workspace.id).where(Membership.user_id == user.id)).all()
    return [{"id": workspace.id, "name": workspace.name, "role": role} for workspace, role in rows]


@app.post("/workspaces", status_code=201)
def create_workspace(payload: WorkspaceCreate, user: User = Depends(authenticated_user), db: Session = Depends(db_session)):
    workspace = Workspace(name=payload.name.strip(), owner_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(Membership(workspace_id=workspace.id, user_id=user.id, role="owner"))
    audit(db, workspace.id, user.id, "workspace.created", "workspace", workspace.id, after={"name": workspace.name})
    db.commit()
    return {"id": workspace.id, "name": workspace.name, "role": "owner"}


@app.get("/projects")
def list_projects(context=Depends(workspace_member)):
    _, member, db = context
    projects = db.scalars(select(Project).where(Project.workspace_id == member.workspace_id, Project.archived.is_(False)).order_by(Project.created_at.desc())).all()
    return [{"id": p.id, "title": p.title, "goal": p.goal, "due_date": p.due_date, "created_at": p.created_at} for p in projects]


@app.post("/projects", status_code=201)
def create_project(payload: ProjectCreate, context=Depends(write_access)):
    user, member, db = context
    project = Project(workspace_id=member.workspace_id, title=payload.title.strip(), goal=payload.goal.strip(), due_date=payload.due_date)
    db.add(project); db.flush()
    audit(db, member.workspace_id, user.id, "project.created", "project", project.id, after={"title": project.title, "goal": project.goal})
    db.commit()
    return {"id": project.id, "title": project.title, "goal": project.goal, "due_date": project.due_date}


@app.get("/milestones")
def list_milestones(context=Depends(workspace_member)):
    _, member, db = context
    rows = db.scalars(select(Milestone).where(Milestone.workspace_id == member.workspace_id).order_by(Milestone.due_date, Milestone.created_at)).all()
    return [{"id": m.id, "project_id": m.project_id, "title": m.title, "acceptance_criteria": m.acceptance_criteria, "baseline_due_date": m.baseline_due_date, "due_date": m.due_date, "status": m.status, "completion_evidence": m.completion_evidence} for m in rows]


@app.post("/milestones", status_code=201)
def create_milestone(payload: MilestoneCreate, context=Depends(write_access)):
    user, member, db = context
    one(db, Project, payload.project_id, member.workspace_id)
    milestone = Milestone(workspace_id=member.workspace_id, project_id=payload.project_id, title=payload.title.strip(), acceptance_criteria=payload.acceptance_criteria.strip(), baseline_due_date=payload.due_date, due_date=payload.due_date)
    db.add(milestone); db.flush()
    audit(db, member.workspace_id, user.id, "milestone.created", "milestone", milestone.id, after={"title": milestone.title, "due_date": str(milestone.due_date) if milestone.due_date else None})
    db.commit()
    return {"id": milestone.id, "title": milestone.title, "due_date": milestone.due_date, "status": milestone.status}


@app.patch("/milestones/{milestone_id}")
def patch_milestone(milestone_id: str, payload: MilestonePatch, context=Depends(write_access)):
    user, member, db = context
    milestone = one(db, Milestone, milestone_id, member.workspace_id)
    before = {"due_date": str(milestone.due_date) if milestone.due_date else None, "status": milestone.status}
    changes = payload.model_dump(exclude_unset=True)
    if "due_date" in changes and changes["due_date"] != milestone.due_date:
        if not changes.get("reason", "").strip():
            raise HTTPException(422, "A reforecast reason is required")
        milestone.due_date = changes["due_date"]
    if changes.get("completion_evidence") is not None:
        evidence = changes["completion_evidence"].strip()
        if not evidence:
            raise HTTPException(422, "Completion evidence is required")
        milestone.completion_evidence = evidence
        milestone.status = "Done"
    audit(db, member.workspace_id, user.id, "milestone.updated", "milestone", milestone.id, before=before, after={"due_date": str(milestone.due_date) if milestone.due_date else None, "status": milestone.status}, reason=changes.get("reason", ""))
    db.commit()
    return {"id": milestone.id, "due_date": milestone.due_date, "status": milestone.status}


@app.get("/tasks")
def list_tasks(context=Depends(workspace_member)):
    _, member, db = context
    tasks = db.scalars(select(Task).where(Task.workspace_id == member.workspace_id).order_by(Task.created_at.desc())).all()
    return [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "project_id": t.project_id, "due_date": t.due_date, "estimate_hours": t.estimate_hours, "dependency_id": t.dependency_id, "completed_at": t.completed_at} for t in tasks]


@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate, context=Depends(write_access)):
    user, member, db = context
    if payload.project_id:
        one(db, Project, payload.project_id, member.workspace_id)
    if payload.dependency_id:
        one(db, Task, payload.dependency_id, member.workspace_id)
    task = Task(workspace_id=member.workspace_id, title=payload.title.strip(), project_id=payload.project_id, priority=payload.priority, due_date=payload.due_date, estimate_hours=payload.estimate_hours, dependency_id=payload.dependency_id)
    db.add(task); db.flush()
    audit(db, member.workspace_id, user.id, "task.created", "task", task.id, after={"title": task.title, "status": task.status})
    db.commit()
    return {"id": task.id, "title": task.title, "status": task.status}


@app.patch("/tasks/{task_id}")
def patch_task(task_id: str, payload: TaskPatch, context=Depends(write_access)):
    user, member, db = context
    task = one(db, Task, task_id, member.workspace_id)
    before = {"status": task.status, "due_date": task.due_date.isoformat() if task.due_date else None, "priority": task.priority}
    data = payload.model_dump(exclude_unset=True)
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            raise HTTPException(422, "Invalid task status")
        if data["status"] in {"In Progress", "Done"} and task.dependency_id:
            dependency = one(db, Task, task.dependency_id, member.workspace_id)
            if dependency.status != "Done":
                raise HTTPException(409, "Finish the dependency before progressing this task")
        task.status = data["status"]
        task.completed_at = datetime.now(timezone.utc) if task.status == "Done" else None
    if "project_id" in data and data["project_id"]:
        one(db, Project, data["project_id"], member.workspace_id)
    for field in ("due_date", "project_id", "priority"):
        if field in data:
            setattr(task, field, data[field])
    audit(db, member.workspace_id, user.id, "task.updated", "task", task.id, before=before, after={"status": task.status, "due_date": task.due_date.isoformat() if task.due_date else None, "priority": task.priority})
    db.commit()
    return {"id": task.id, "status": task.status, "due_date": task.due_date}


@app.get("/notes")
def list_notes(context=Depends(workspace_member)):
    _, member, db = context
    notes = db.scalars(select(Note).where(Note.workspace_id == member.workspace_id, Note.archived.is_(False)).order_by(Note.created_at.desc())).all()
    return [{"id": n.id, "title": n.title, "body": n.body, "project_id": n.project_id, "created_at": n.created_at} for n in notes]


@app.post("/notes", status_code=201)
def create_note(payload: NoteCreate, context=Depends(write_access)):
    user, member, db = context
    if payload.project_id:
        one(db, Project, payload.project_id, member.workspace_id)
    note = Note(workspace_id=member.workspace_id, title=payload.title.strip(), body=payload.body, project_id=payload.project_id)
    db.add(note); db.flush()
    audit(db, member.workspace_id, user.id, "note.created", "note", note.id, after={"title": note.title})
    db.commit()
    return {"id": note.id, "title": note.title}


@app.get("/members")
def list_members(context=Depends(workspace_member)):
    _, member, db = context
    rows = db.scalars(select(Membership).where(Membership.workspace_id == member.workspace_id).order_by(Membership.role, Membership.user_id)).all()
    return [{"user_id": row.user_id, "role": row.role} for row in rows]


@app.post("/members", status_code=201)
def add_member(payload: MemberCreate, context=Depends(workspace_member)):
    user, membership, db = context
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(403, "Only an owner or admin can add members")
    if db.get(User, payload.user_id) is None:
        raise HTTPException(422, "The invited user must authenticate before being added")
    existing = db.scalar(select(Membership).where(Membership.workspace_id == membership.workspace_id, Membership.user_id == payload.user_id))
    if existing:
        raise HTTPException(409, "User is already a member")
    row = Membership(workspace_id=membership.workspace_id, user_id=payload.user_id, role=payload.role)
    db.add(row); db.flush()
    audit(db, membership.workspace_id, user.id, "member.added", "membership", row.id, after={"user_id": row.user_id, "role": row.role})
    db.commit()
    return {"user_id": row.user_id, "role": row.role}


@app.get("/call-preferences")
def get_call_preferences(context=Depends(workspace_member)):
    user, member, db = context
    preference = pref_for(db, member.workspace_id, user.id)
    db.commit()
    return {"phone": preference.phone, "timezone": preference.timezone, "calls_consent": preference.calls_consent, "recording_consent": preference.recording_consent, "paused": preference.paused, "allowed_from": preference.allowed_from, "allowed_to": preference.allowed_to, "daily_max": preference.daily_max, "weekly_max": preference.weekly_max}


@app.patch("/call-preferences")
def patch_call_preferences(payload: CallPreferencePatch, context=Depends(workspace_member)):
    user, member, db = context
    preference = pref_for(db, member.workspace_id, user.id)
    before = {"calls_consent": preference.calls_consent, "recording_consent": preference.recording_consent, "paused": preference.paused}
    changes = payload.model_dump(exclude_unset=True)
    if "timezone" in changes:
        try:
            ZoneInfo(changes["timezone"])
        except ZoneInfoNotFoundError as error:
            raise HTTPException(422, "Unknown timezone") from error
    for field, value in changes.items():
        setattr(preference, field, value)
    audit(db, member.workspace_id, user.id, "call_preferences.updated", "call_preference", preference.id, before=before, after={"calls_consent": preference.calls_consent, "recording_consent": preference.recording_consent, "paused": preference.paused})
    db.commit()
    return {"phone": preference.phone, "timezone": preference.timezone, "calls_consent": preference.calls_consent, "recording_consent": preference.recording_consent, "paused": preference.paused, "allowed_from": preference.allowed_from, "allowed_to": preference.allowed_to, "daily_max": preference.daily_max, "weekly_max": preference.weekly_max}


@app.get("/privacy/export")
def privacy_export(context=Depends(workspace_member)):
    user, member, db = context
    # This export is intentionally workspace-scoped and excludes secrets and security logs.
    tasks = db.scalars(select(Task).where(Task.workspace_id == member.workspace_id)).all()
    projects = db.scalars(select(Project).where(Project.workspace_id == member.workspace_id)).all()
    notes = db.scalars(select(Note).where(Note.workspace_id == member.workspace_id)).all()
    calls = db.scalars(select(Call).where(Call.workspace_id == member.workspace_id)).all()
    audit(db, member.workspace_id, user.id, "privacy.exported", "workspace", member.workspace_id, source="privacy")
    db.commit()
    return {"workspace_id": member.workspace_id, "exported_at": datetime.now(timezone.utc), "projects": [{"id": p.id, "title": p.title, "goal": p.goal} for p in projects], "tasks": [{"id": t.id, "title": t.title, "status": t.status, "due_date": t.due_date} for t in tasks], "notes": [{"id": n.id, "title": n.title, "body": n.body} for n in notes], "calls": [{"id": c.id, "mode": c.mode, "state": c.state, "reasons": c.reasons} for c in calls]}


@app.post("/calls", status_code=201)
def request_call(payload: CallRequest, context=Depends(write_access)):
    user, member, db = context
    preference = pref_for(db, member.workspace_id, user.id)
    reasons = call_policy(db, member.workspace_id, user.id, preference)
    # The call is deliberately a dry-run until a reviewed provider adapter is deployed.
    reasons.append("Telephony is not configured in this deployment")
    call = Call(workspace_id=member.workspace_id, mode=payload.mode, state="rejected_by_policy", reasons=reasons)
    db.add(call); db.flush()
    audit(db, member.workspace_id, user.id, "call.rejected_by_policy", "call", call.id, after={"mode": call.mode, "reasons": call.reasons}, source="policy_engine")
    db.commit()
    return {"id": call.id, "state": call.state, "reasons": call.reasons}


@app.get("/audit")
def list_audit(context=Depends(workspace_member)):
    _, member, db = context
    events = db.scalars(select(AuditEvent).where(AuditEvent.workspace_id == member.workspace_id).order_by(AuditEvent.created_at.desc()).limit(200)).all()
    return [{"id": e.id, "action": e.action, "entity": e.entity, "entity_id": e.entity_id, "before": e.before, "after": e.after, "reason": e.reason, "source": e.source, "correlation_id": e.correlation_id, "created_at": e.created_at} for e in events]


@app.get("/report/weekly")
def weekly_report(context=Depends(workspace_member)):
    _, member, db = context
    tasks = db.scalars(select(Task).where(Task.workspace_id == member.workspace_id)).all()
    today = date.today()
    completed = [t for t in tasks if t.status == "Done"]
    overdue = [t for t in tasks if t.status not in {"Done", "Cancelled"} and t.due_date and t.due_date <= today]
    blocked = [t for t in tasks if t.status == "Blocked"]
    return {"completed": len(completed), "overdue": len(overdue), "blocked": len(blocked), "generated_at": datetime.now(timezone.utc), "definition": "Counts are computed from workspace-scoped task records; no AI estimate is included."}
