"""Regression tests for the core MVP safety boundary."""
import os
import tempfile
import unittest
from pathlib import Path

DB_FILE = Path(tempfile.gettempdir()) / "orbit_api_regression_test.db"
if DB_FILE.exists():
    DB_FILE.unlink()
os.environ["ORBIT_DATABASE_URL"] = f"sqlite:///{DB_FILE}"
os.environ["ORBIT_ALLOW_DEV_AUTH"] = "true"

from fastapi.testclient import TestClient  # noqa: E402
from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)


class OrbitApiTests(unittest.TestCase):
    def setUp(self):
        self.client_context = TestClient(app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)

    def workspace(self, user: str) -> tuple[dict, dict]:
        identity = {"X-Orbit-Dev-User": user}
        response = self.client.post("/workspaces", headers=identity, json={"name": f"{user} workspace"})
        self.assertEqual(response.status_code, 201, response.text)
        return identity, {**identity, "X-Orbit-Workspace": response.json()["id"]}

    def test_workspace_records_and_report(self):
        _, headers = self.workspace("test-owner")
        project = self.client.post("/projects", headers=headers, json={"title": "Launch", "goal": "Ship safely"})
        self.assertEqual(project.status_code, 201, project.text)
        task = self.client.post("/tasks", headers=headers, json={"title": "Verify", "project_id": project.json()["id"], "priority": 3})
        self.assertEqual(task.status_code, 201, task.text)
        complete = self.client.patch(f"/tasks/{task.json()['id']}", headers=headers, json={"status": "Done"})
        self.assertEqual(complete.status_code, 200, complete.text)
        report = self.client.get("/report/weekly", headers=headers)
        self.assertEqual(report.status_code, 200, report.text)
        self.assertEqual(report.json()["completed"], 1)

    def test_workspace_cannot_be_read_by_another_user(self):
        _, owner = self.workspace("private-owner")
        task = self.client.post("/tasks", headers=owner, json={"title": "Private task"})
        attacker = {"X-Orbit-Dev-User": "not-a-member", "X-Orbit-Workspace": owner["X-Orbit-Workspace"]}
        self.assertEqual(self.client.get("/tasks", headers=attacker).status_code, 403)
        self.assertEqual(self.client.patch(f"/tasks/{task.json()['id']}", headers=attacker, json={"status": "Done"}).status_code, 403)

    def test_call_path_is_safe_by_default(self):
        _, headers = self.workspace("call-safety")
        pref = self.client.patch("/call-preferences", headers=headers, json={"phone": "+919999999999", "calls_consent": True})
        self.assertEqual(pref.status_code, 200, pref.text)
        call = self.client.post("/calls", headers=headers, json={"mode": "on_demand"})
        self.assertEqual(call.status_code, 201, call.text)
        self.assertEqual(call.json()["state"], "rejected_by_policy")
        self.assertTrue(any("Telephony is not configured" in reason for reason in call.json()["reasons"]))

    def test_milestone_needs_evidence_to_complete(self):
        _, headers = self.workspace("milestone-owner")
        project = self.client.post("/projects", headers=headers, json={"title": "Release"})
        milestone = self.client.post("/milestones", headers=headers, json={"project_id": project.json()["id"], "title": "Acceptance", "due_date": "2026-12-31"})
        self.assertEqual(milestone.status_code, 201, milestone.text)
        rejected = self.client.patch(f"/milestones/{milestone.json()['id']}", headers=headers, json={"completion_evidence": ""})
        self.assertEqual(rejected.status_code, 422)
        done = self.client.patch(f"/milestones/{milestone.json()['id']}", headers=headers, json={"completion_evidence": "Test evidence"})
        self.assertEqual(done.status_code, 200, done.text)
        self.assertEqual(done.json()["status"], "Done")

    def test_ai_is_disabled_without_explicit_configuration(self):
        _, headers = self.workspace("ai-safety")
        response = self.client.post("/ai/plan-drafts", headers=headers, json={"goal": "Ship a safe MVP", "capacity_hours": 5})
        self.assertEqual(response.status_code, 503, response.text)


if __name__ == "__main__":
    unittest.main()
