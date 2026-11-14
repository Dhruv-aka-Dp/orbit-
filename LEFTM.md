# Orbit implementation board

This board separates completed repository work from the work still required to call Orbit a fully launched commercial product. Percentages describe delivery maturity, not a promise of launch readiness.

## Overall progress

```text
Repository foundation   ████████████░░░░░░░░  60%
User-facing MVP         ████████░░░░░░░░░░░░  40%
Production operations   ██████░░░░░░░░░░░░░░  30%
AI capability           ██████░░░░░░░░░░░░░░  30%
Voice calling           ██░░░░░░░░░░░░░░░░░░  10%
Public launch           ██░░░░░░░░░░░░░░░░░░  10%
```

## Completed in the repository

| Area | Delivered |
| --- | --- |
| Product data | Workspace-scoped projects, tasks, dependencies, notes and milestones |
| Evidence | Completion evidence, append-only audit events and deterministic weekly report |
| Access boundary | Membership records, roles, server-side workspace membership checks and OIDC bearer-token validation |
| Privacy baseline | Workspace export endpoint, consent preferences, recording off by default in the data model |
| Call safety | Quiet-window, consent, pause and frequency-limit policy evaluation; safe rejection while no carrier is active |
| AI safety | Read-only OpenAI Responses API plan drafts, no model tools that can mutate data or contact third parties |
| Deployment foundation | Docker Compose, Postgres, Nginx proxy, health endpoint, development/production environment templates |
| Database | Alembic baseline migration and migration command |
| Quality | Five API/safety tests, Python/JavaScript/shell syntax checks and GitHub Actions CI |
| Operations | Start, stop, status, logs, build, test, migration, backup, restore and guarded deployment scripts |

## Build next in the repository

| Priority | Work remaining | Why it matters |
| --- | --- | --- |
| P0 | Browser OIDC Authorization Code + PKCE sign-in and sign-out | The API validates bearer tokens, but the browser does not yet acquire them itself |
| P0 | PostgreSQL Row-Level Security policies and database-role design | Current tenant checks are application-level, not database-enforced RLS |
| P0 | Forward-only migration revisions for every future schema change | The initial migration exists; release changes must not use `create_all` |
| P0 | Concrete carrier adapter, signed webhook inbox, idempotency and reconciliation | Required before any actual telephone call |
| P0 | STT, TTS, real-time audio gateway, barge-in and call-state persistence | Required for the voice-agent experience described in the specification |
| P0 | Job queue, scheduler, retry/backoff, outbox and dead-letter handling | Required for scheduled calls, reports and reliable async processing |
| P1 | Complete web UI for milestones, memberships, call preferences, privacy export and AI drafts | Backend support exists but the browser does not expose every workflow |
| P1 | Planner, recurring tasks, calendar integration and automation rule engine | Core product experience is not complete without planning/automation |
| P1 | Rich documents, attachments, object storage, search and retention propagation | Notes are plain text today |
| P1 | AI draft review/approval UI and evaluation harness | AI output must remain reviewable before it becomes product data |
| P1 | Billing, entitlement checks, quotas and usage metering | Needed before charging customers or controlling expensive voice/AI use |
| P1 | Browser E2E, accessibility, load, failure-recovery and security test suites | Five API tests are not sufficient release coverage |
| P2 | Team invitations, ownership transfer, SSO administration and enterprise controls | Needed for team/business packaging |
| P2 | Mobile app, additional languages, additional speech providers and second carrier | Post-launch expansion work |

## External release work

These cannot be completed from source code alone:

- Trademark/domain clearance, privacy/telecom counsel and published legal terms.
- Cloud account, production network, managed database, KMS/secrets, DNS/TLS/WAF and monitoring provider setup.
- Identity-provider and carrier accounts, contracts, API credentials, phone numbers and production approvals.
- Backup restore drill, penetration test, support/on-call ownership and controlled canary cohort.

The full checkable release sequence is in [MANUAL_RELEASE_STEPS.md](MANUAL_RELEASE_STEPS.md).

## Definition of done

Orbit is ready for public paid customers only when every P0 item above is complete, the external release list is signed off, the staging release passes the full test/recovery/security suite, and the carrier/legal approvals explicitly permit the intended AI calling route.
