# Free backend implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, then one fresh whole-branch review. User has authorized design decisions and proceeding.

**Goal:** Create a deployable $0-base-cost online backend for the existing Pages entry page.

**Architecture:** SQLite remains local. A PostgreSQL adapter supplies private per-account schemas, transactional queue operations, durable sessions, and account discovery to the existing API/worker. Render Free runs the container; Supabase Free stores structured data.

**Tech Stack:** Python 3.12, psycopg 3, PostgreSQL, FastAPI/Authlib, React/Vite, Render Free, Supabase Free.

**Spec:** docs/superpowers/specs/2026-10-03-free-backend-design.md

## Global constraints

- Hosting base cost $0; no card, paid upgrades, artificial keepalive, or paid resources.
- Preserve SQLite local data, local uploads, and existing Google account isolation.
- Hosted database encrypted; credentials stay server-side and ignored.
- Free hosted original video uploads disabled; YouTube and SRT/VTT supported.
- Connect Pages only after backend is healthy and configured.

## Review focus

1. Local filesystem disappears: private libraries and login states must persist remotely.
2. Concurrent duplicate requests and claims: exactly one handoff/job claimant.
3. Database outage: generic 503, no connection string in response.
4. Different accounts: all lecture/job/session lookups remain isolated.
5. Free deployment: no disk or paid default, unsupported uploads rejected before spooling.

### Task 1: Durable PostgreSQL storage

**Files:** backend/app/database.py, storage.py, sessions.py, jobs.py; backend/tests/test_postgres.py; backend/requirements.txt and requirements.lock; .github/workflows/hosting-checks.yml.

**Interfaces:** Database(path, database_url='', namespace='root').connection() yields execute/executescript/iteration-compatible connection. Repository(path, database_url='', workspace_id='root') retains existing methods. SessionStore(path, database_url='') retains existing methods. AccountRegistry(database_url).register(hash)/list() provides durable identities.

- [ ] Write failing real PostgreSQL tests for restart persistence, two-account isolation, concurrent handoff and claims, precise session expiry, one-use OAuth state, and generation rollback.
- [ ] Run tests against real PostgreSQL in CI; initially fail on missing interface.
- [ ] Implement adapter with explicit insert columns, private schemas, schema transaction advisory locks, dict rows and DOUBLE PRECISION expiry.
- [ ] Pin driver, run existing local tests, and commit.

### Task 2: Hosted API/worker integration and free limits

**Files:** backend/app/config.py, auth.py, worker.py, main.py, routes.py; web/src/App.tsx, api.ts, features/import/ImportPanel.tsx; backend/tests/test_free_hosting.py; web/src/App.test.tsx.

**Interfaces:** Config.database_url SecretStr, workspace_id string, video_uploads_enabled bool. repository_for(config) constructs correct backend. workspace(config,sub) hashes Google sub and registers it. Health authenticated response adds video_uploads_enabled. Worker remote discovery uses AccountRegistry.

- [ ] Write/run failing tests for free upload rejection before body parsing, local upload preservation, missing/unencrypted hosted database URL validation, outage response, and worker recovery after local directory deletion.
- [ ] Integrate repository factories, session storage and durable discovery. Handle remote database errors with generic 503 and truthful health status.
- [ ] Show free online limits in import UI and retain local controls; run frontend tests/builds and backend suite.
- [ ] Commit validated changes.

### Task 3: Free deployment and review

**Files:** render.yaml, HOSTING.md, README.md, VERIFICATION.md, scripts/container_check.py; .github/workflows/hosting-checks.yml.

**Interfaces:** DATABASE_URL uses Supabase IPv4 session pooler with TLS; free blueprint no disk. CI PostgreSQL service provides TEST_DATABASE_URL; Docker smoke uses host network disposable DB.

- [ ] Configure free-only blueprint and real container PostgreSQL persistence smoke checks. Run local suites, audit tracked/build artifacts for secrets, push feature branch and inspect CI.
- [ ] Request fresh read-only review against spec/plan; fix material findings with regression tests.
- [ ] Integrate reviewed source after passing CI. Prepare Supabase/Google/Render setup and perform authorized free setup where credentials allow.
- [ ] Verify live flow before connecting Pages; record exact account or credential steps if blocked, with no claim of live functionality.
