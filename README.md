# Orbit

Orbit is a consent-first personal productivity platform. It combines projects, tasks, notes, milestones, deterministic reports and an audit trail in workspace-scoped API services.

> Current state: **runnable MVP foundation**. It is not yet a public production launch; live telephony and browser OIDC sign-in remain release-gated.

## What works today

- Multi-workspace API with server-side membership checks and role-aware writes.
- Projects, tasks, dependencies, notes, milestones and completion evidence.
- Audit events, deterministic weekly reports and privacy export.
- Personal calling preferences and a safe call-policy evaluation path.
- Read-only AI plan-draft endpoint, enabled only when an OpenAI API key and model are configured.
- Docker-based local stack, database migration, tests, CI and local operational scripts.

## Quick start

1. Start Docker Desktop.
2. Run `./scripts/start.sh`.
3. Open `http://localhost:8080`.
4. Verify it with `./scripts/status.sh` and `./scripts/test.sh`.

The first start creates a local `.env` from `.env.example`. This is development-only; do not deploy it.

## Commands

| Command | Purpose |
| --- | --- |
| `./scripts/start.sh` | Build, migrate and start the local stack |
| `./scripts/stop.sh` | Stop the local stack |
| `./scripts/status.sh` | Show containers and API health |
| `./scripts/logs.sh [service]` | Follow logs |
| `./scripts/test.sh` | Run backend tests in the API container |
| `./scripts/lint.sh` | Run static syntax checks |
| `./scripts/ci-local.sh` | Run lint and tests together |
| `./scripts/migrate.sh` | Apply Alembic migrations |
| `./scripts/backup.sh` | Create a local PostgreSQL backup |
| `./scripts/restore.sh file.sql` | Restore a confirmed local backup |
| `./scripts/build.sh` | Rebuild images |
| `./scripts/clean-local.sh` | Delete the local database after confirmation |

`deploy-staging.sh` and `deploy-production.sh` deliberately require a reviewed cloud deployment command. They do not guess cloud accounts, domains or production targets.

## AI and calls

The AI plan-draft endpoint uses the OpenAI Responses API as a read-only draft generator. Set `OPENAI_API_KEY` and `ORBIT_OPENAI_MODEL` in the local `.env` to enable it. It has no database-write, shell, external-message, or purchasing tools. See the [official OpenAI Python API documentation](https://developers.openai.com/api/reference/python).

Telephone calls are **not live**. The application includes consent preferences, policy checks and a provider interface, but it intentionally rejects outbound calls until the selected carrier, webhook implementation, speech pipeline, security testing and legal approval are complete.

## Project progress

See [LEFTM.md](LEFTM.md) for the detailed implementation board and [MANUAL_RELEASE_STEPS.md](MANUAL_RELEASE_STEPS.md) for account-holder, provider, legal and launch tasks.

## Repository map

```text
app/                 Browser client
backend/app/         FastAPI domain/API code
backend/alembic/     Versioned database schema migrations
backend/tests/       Automated API/safety tests
scripts/             Local lifecycle and operational commands
deploy/              Reverse-proxy configuration
spec/                Product and technical specification
pitch-deck/          Investor-deck source
```
