# Private Render backend implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement these tasks with test-first verification and one final independent review.

**Goal:** Connect the Pages entry screen to a privately authenticated Render processing app.

**Architecture:** One Docker service supervises FastAPI and the worker on a persistent disk. Google OIDC authenticates invited accounts; opaque revocable sessions protect their separate libraries. Pages posts a constrained video handoff to Render; the authenticated app imports it once.

**Tech stack:** React/TypeScript, FastAPI, SQLite, Authlib OIDC, Docker, Render.

**Spec:** ../specs/2026-10-03-private-hosting-google-design.md

## Constraints and rulings

- Preserve the local app and existing library; local startup needs no OAuth configuration.
- Hosted startup fails closed without required settings. Never commit actual credentials or owner email.
- Hosted sessions last 24 hours; temporary OAuth state lasts 10 minutes. Use HTTPS, Secure/HttpOnly session cookies, CSRF checks, and exact approved identity.
- Ruling: the user clarified that each user's email should access their own data. Use the verified Google subject as the stable account ID, separate hashed account directories and databases, and invitations by default. Email is displayed and used for invitations; it is not trusted as an identity supplied by the browser. No payments or automatic local-library transfer.
- Keep the existing source/public visibility and Pages URL. Hosting provisioning and actual Google login need user-owned accounts/secrets and an approved paid service.
- Ruling: the user approved the design and subsequent routine decisions on October 3 and requested proceeding; execute natively without another design/plan approval loop.
- Ruling: work in the existing project checkout on feature/render-backend. This projectless chat's native worktree tool cannot target the nested app repository; keep main untouched until checks and review pass.

## Review focus

Replayed sign-in/handoff must not enqueue duplicate jobs; missing origin cannot bypass CSRF; a changed owner setting revokes prior identity access; a dead worker must make hosted health fail; published Pages assets must never include secrets or a backend URL before that service works.

### Task 1: Hosted configuration and Google access

- [ ] Add failing tests for missing hosted settings, signed-out API/media denial, owner-only identity, session expiration/tampering/logout, CSRF and exact Host/origin checks.
- [ ] Implement config validation, SQLite session store, Authlib Google login/callback, and authentication middleware. Test Google token validation at the real OAuth boundary with controlled HTTP/JWT fixtures; never patch out cryptographic verification in its regression tests.
- [ ] Run the full Python suite and record results; commit the authenticated backend.

Files: backend/app/config.py, main.py, auth.py, sessions.py; backend/tests/test_hosting.py; backend/requirements.txt and lock.

### Task 2: Pages handoff and protected interface

- [ ] Add failing tests for cross-origin/invalid handoff rejection and idempotent import; tests for signed-out Google button and configured/unconfigured Pages submission.
- [ ] Implement constrained POST /start, one-time POST /api/handoff, /auth/session and logout, React AuthGate, Pages form destination, and authenticated CSRF headers.
- [ ] Run backend/frontend suites and both production builds; commit the interface integration.

Files: backend/app/auth.py and handoff.py; web/src/AuthGate.tsx, api.ts, PagesEntry.tsx and tests, main.tsx.

### Task 3: Process supervision and deployment

- [ ] Add failing executable supervisor tests for child failure and signal shutdown; health tests for stale worker heartbeat.
- [ ] Implement supervisor, worker availability health, multi-stage Docker build with FFmpeg, persistent temporary storage, .dockerignore, Render template, and GitHub container-build smoke checks.
- [ ] Document Google client/callback setup, service cost confirmation, secrets, Pages URL configuration, backup/restore, and exact live checks. Build and run the container in a supported environment before claiming container verification.

Files: scripts/serve.py, Dockerfile, .dockerignore, render.yaml, .github/workflows/hosting-checks.yml, HOSTING.md, backend/tests/test_supervisor.py.

### Task 4: Review and delivery

- [ ] Review the whole change independently; fix significant findings with regression checks.
- [ ] Scan Git history and built assets for secrets; fast-forward/push reviewed source if remote main remains unchanged.
- [ ] Verify GitHub CI/container evidence. Preserve the unconnected Pages notice until the real service and OAuth login work.
- [ ] Complete all source/setup work before requesting the user's final account/secrets/billing step. Report actual deployment status and any external blockers clearly.
