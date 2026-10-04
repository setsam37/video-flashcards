# Free backend design

The user wants the GitHub Pages video entry screen to create real lessons online, with Google account libraries, at the lowest recurring hosting cost. They authorized design decisions and asked to research and proceed. That authorization supersedes repeated skill approval gates. Implement inline and obtain one independent review before integration.

## Choice and cost

Keep Pages, run the existing Python app and worker together on Render Free, and persist structured data in Supabase Free PostgreSQL. Render is already connected to the user's account. Koyeb also offers a small free container but requires a payment method and has no free volume. Render Free PostgreSQL expires after 30 days; it is unsuitable for permanent lessons. A local PC and tunnel costs no hosting fee but depends on the PC remaining on. Render plus Supabase avoids that dependency and avoids a rewrite to another runtime.

Hosting base cost is $0 within free limits. OpenAI usage is billed separately. Render sleeps after 15 minutes and wakes in approximately a minute; its filesystem is ephemeral. Supabase has 500 MB database space and may pause after a week of inactivity. No card, paid upgrade, artificial keepalive, or paid resource is authorized.

Sources: https://render.com/docs/free, https://supabase.com/pricing, https://www.koyeb.com/docs/faqs/pricing, https://www.koyeb.com/docs/reference/instances.

## Persistence

Keep SQLite and the existing data layout in local mode. Add PostgreSQL through a focused database adapter, using psycopg 3 and dict rows, with schema names derived solely from a validated account hash. Persist lessons, transcripts, syllabus, cards, gaps, completed ranges, jobs, handoff deduplication, opaque login sessions, and one-use OAuth states. Use private schemas outside Supabase's exposed public API. Require encrypted database connections in hosted mode. Do not expose credentials to the frontend or commit secrets.

Transactions that currently use SQLite BEGIN IMMEDIATE acquire a PostgreSQL transaction advisory lock per schema. This preserves atomic queue claims, duplicate handoffs, and generation replacement with the existing single-worker deployment. Explicit insertion columns and a generated ordering column make SQL portable. Session expiry uses DOUBLE PRECISION on PostgreSQL. The worker discovers accounts through a durable registry instead of scanning local directories. On container restart, interrupted jobs become retryable; completed chapter results remain saved.

## Free online scope

Support YouTube URLs and SRT/VTT caption imports with YouTube playback. Disable original video uploads on the ephemeral free server at both UI and request boundary, with clear copy pointing to the local app. Preserve full local upload/transcription functionality. Uploaded original videos would need separate storage and a larger processing budget and are outside this free first release. Transcript text is stored in PostgreSQL. Successful completed selections are reused as before.

## Deployment and errors

Default Render blueprint uses plan free, no disk, DATA_DIR=/tmp/recall, VIDEO_UPLOADS_ENABLED=false, and a private DATABASE_URL supplied by the user. Keep invitations and Google login protection. Request errors from database outages must be a generic 503, never a credential-bearing driver message. Startup fails safely when required configuration is missing. Health checks cover database and worker. Only connect Pages after a real backend is healthy and configured.

Account signup, database password entry, Google OAuth credentials, and any terms acceptance remain user-owned. Prepare code, tests, and instructions before any unavoidable handoff. Do not claim live Google auth or real provider generation without observing it.

## Verification

Run existing local/auth/frontend tests. Add PostgreSQL integration tests against a real disposable PostgreSQL service in GitHub Actions: persistence after deleting the local working directory, account isolation, concurrent handoff/queue claims, session and OAuth-state persistence/expiry, registry discovery, interruption recovery, and generation rollback. Exercise the real Docker container with an external PostgreSQL service. Test online upload rejection and local preservation. Independent review checks concurrency, private data boundaries, restart recovery, free resource configuration, and secret handling.
