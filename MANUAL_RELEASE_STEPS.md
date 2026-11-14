# Orbit release handoff

This is the finite list of work that cannot be completed from this workspace because it needs an account holder, a regulated provider, a cloud administrator, or qualified legal advice. Do not replace any item with a self-attestation.

## Release blockers

- [ ] Clear the Orbit name and domain in every launch jurisdiction. The working name is not cleared by this repository.
- [ ] Obtain written India call classification, number-provisioning, sender/consent and AI-voice approval from the selected carrier/provider. Do not enable outbound calls before this is received.
- [ ] Obtain privacy and telecom counsel approval for the notice, consent wording, recording policy, retention schedule, deletion workflow and incident process.
- [ ] Select the cloud account, India-region data locations, subprocessors, support owner and on-call owner.
- [ ] Create a managed PostgreSQL instance, private network, managed secrets store, KMS keys, encrypted object storage and a separate backup account/failure domain.
- [ ] Run a reviewed, forward-only database migration from the ORM models before first production traffic. Do not use development `create_all` in production.
- [ ] Configure an OIDC client or identity-aware edge proxy. It must issue a bearer JWT with the configured issuer and audience, send it to the API as `Authorization: Bearer …`, and register the exact public redirect URL if browser sign-in is used.
- [ ] Set production secrets and configuration: `POSTGRES_PASSWORD`, `ORBIT_DATABASE_URL`, `ORBIT_OIDC_ISSUER`, `ORBIT_OIDC_AUDIENCE`, `ORBIT_OIDC_CLIENT_ID`, `ORBIT_OIDC_REDIRECT_URI`, `ORBIT_CORS_ORIGINS`, `ORBIT_ENV=production`, and `ORBIT_ALLOW_DEV_AUTH=false`.
- [ ] Put TLS, WAF/rate limiting, DNS, health checks and an external status page in front of the web service.
- [ ] Configure centralized, redacted logs; metrics; tracing; security alerts; error tracking; and backup/PITR monitoring. Test alert routing with the on-call owner.
- [ ] Run dependency/container scanning, secret scanning, a penetration test, accessibility checks and a cross-tenant security test against the deployed environment.
- [ ] Restore a production-like backup into an isolated account and record the observed RPO/RTO.
- [ ] Publish terms, privacy notice, support contact, data-export/deletion process, call/recording disclosures and incident communication process.

## Telephony activation gate

The source intentionally contains only the provider interface. Before implementing and enabling a concrete adapter:

- [ ] Sign the provider agreement and validate account, number, call classification, throughput, WebSocket media format, webhook signature, recording behaviour, data-processing terms, pricing and service limits.
- [ ] Implement a provider-specific adapter that verifies every webhook before processing it, uses idempotency keys, persists a webhook inbox, and has a provider sandbox test suite.
- [ ] Provision and verify internal test numbers. Configure hard daily spend caps, a global call kill switch, quiet-hour and quota enforcement, and opt-out suppression.
- [ ] Complete an end-to-end test call with the final consent text, interruption behaviour, transcript/recording controls, failure handling and a user-confirmed task update.
- [ ] Obtain documented product, security, provider and legal sign-off before any customer telephone call.

## Launch sequence

1. Deploy to staging with synthetic data and allowlisted test users only.
2. Run the API test suite, browser journey tests, load tests and recovery tests in staging.
3. Apply the signed production migration, then deploy immutable API and web image digests.
4. Smoke-test OIDC, workspace creation, tenant isolation, task updates, reports, audit events, export and disabled-call policy.
5. Start with a small, consented canary cohort. Keep call spend caps and the kill switch enabled.
6. Promote only after the release owner reviews errors, latency, opt-outs, unwanted-call signals and backup monitoring.

## Never enable by configuration alone

Do not turn on real calls, recording, transcript retention, external messaging, payments, automatic deletion, or broad AI write access merely by setting an environment variable. Each needs the corresponding implementation, tests and release approval.
