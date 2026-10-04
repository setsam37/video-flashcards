# Free hosting: GitHub Pages, Render, and Supabase

The starting page stays at https://setsam37.github.io/video-flashcards/. Render runs the app and processing worker; Supabase stores private lessons, transcripts, cards, jobs, and login sessions. After submitting the Pages form, the browser navigates to Render, where Google login and private APIs use first-party session cookies.

The default `render.yaml` requests **Render Free, no disk, no paid database**. Supabase Free supplies PostgreSQL. Base hosting cost is $0 within free limits. OpenAI processing is billed separately. Preparing this source does not create cloud accounts, a live backend, or a Google OAuth client. Pages remains unconnected until live verification passes.

## Free limits

- Render sleeps after 15 minutes without inbound traffic; waking normally takes about a minute. Its local filesystem disappears after sleep/restart/redeployment, and free instances cannot have persistent disks. The workspace receives 750 free instance hours monthly. Free Render Postgres expires after 30 days, so do not use it for your saved lessons.
- Supabase Free includes 500 MB database space, 5 GB egress, and can pause inactive projects after a week. Resume a paused project in its dashboard. Free automatic backups are not included.
- Online import supports **YouTube links and SRT/VTT captions**, with YouTube playback. Original MP4/WebM uploads and audio transcription remain available in the local app. This avoids storing large videos or processing large uploads on the small free server.
- Only generate the chapters you want. Completed ranges are reused. Interrupted jobs become retryable and retain completed chapters; a provider request in flight when the server stops can still incur a charge and may be repeated on retry.
- Do not add paid resources, payment details, or keepalive services to work around these limits. Usage above a free allowance can interrupt service. Check each provider's current limits before changing plans.

Sources: [Render Free](https://render.com/docs/free), [Supabase pricing](https://supabase.com/pricing).

## Prepare Supabase

1. Sign in to [Supabase](https://supabase.com/dashboard), create or select a **Free organization**, then create a dedicated Free project named `Recall`. Choose a US region near the Render service. Enter a strong database password privately and retain it in your password manager.
2. In the project's **Connect** panel, select **Session pooler** (IPv4, port **5432**). Copy its PostgreSQL connection URI. Replace the password placeholder privately, URL-encoding special characters, and append `?sslmode=require` (or `&sslmode=require` if it already has a query). This encrypts the connection. For server identity verification, prefer `sslmode=verify-full` with Supabase's database CA certificate supplied privately as `sslrootcert`; encryption alone does not verify the certificate/hostname. This connection string is a secret. Use the session pooler, not the transaction pooler on port 6543; the worker needs a session-level advisory lock.
3. Supply the URI as `DATABASE_URL` in Render's private environment settings. Do not put it in Pages, GitHub Actions variables, chat, or tracked files.
4. The app creates private `recall_<hash>` schemas automatically. Leave those schemas out of Supabase's exposed API schemas. The app revokes schema/table access from public, anonymous, and authenticated API roles. It connects server-side using the database owner; no Supabase service-role key or browser database client is needed.

See [Supabase connection options](https://supabase.com/docs/guides/database/connecting-to-postgres). Keep a dedicated project so the app's owner connection and backups are separate from unrelated databases.

## Prepare Render and Google login

1. In [Render](https://dashboard.render.com), choose **New → Web Service**, use the public repository `https://github.com/setsam37/video-flashcards`, branch `main`, runtime **Docker**, and instance **Free**. Choose Ohio when available. Review that the summary has **no disk and $0 instance cost**. The blueprint describes these settings but its secret-entry screen may require all settings before creation.
2. Obtain the actual service HTTPS origin from Render. In [Google Auth Platform](https://console.cloud.google.com/auth/overview), configure a web application's consent screen and testing audience, adding invited accounts as test users. Create a **Web application** OAuth client with the exact redirect URI `https://YOUR-ACTUAL-SERVICE.onrender.com/auth/callback`. The Pages URL is not the callback.
3. Set these private environment values in Render:

   - `APP_MODE=hosted`
   - `DATA_DIR=/tmp/recall`
   - `EPHEMERAL_HOSTING=true`
   - `VIDEO_UPLOADS_ENABLED=false`
   - `DATABASE_URL` from Supabase's encrypted session-pooler connection
   - `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from Google
   - `OPENAI_API_KEY` from your existing key or a project key with a usage budget
   - `SESSION_SECRET`: a generated random secret of at least 32 characters, stable across redeployments (the blueprint generates it)
   - `PAGES_ORIGIN=https://setsam37.github.io`
   - `ALLOWED_EMAILS`: JSON array of invited addresses, e.g. `["your-account@example.com"]`
   - `PUBLIC_SIGNUP=false`

4. Set the health-check path to `/api/health`, keep **one instance**, and deploy. `PUBLIC_APP_URL` defaults to Render's `RENDER_EXTERNAL_URL`; override only for an actual custom HTTPS origin. Missing credentials or unsafe free-storage settings stop startup.

Google email controls invitations and is displayed in the app. The verified Google account subject owns the library, independently of IP address. The local library is not automatically uploaded. Keep invitations enabled: every user's generation uses your OpenAI account, and there is no per-user billing quota. Public signup requires a separate decision.

## Verify before connecting Pages

1. Signed out, `/api/health` returns HTTP 200 and only `{"status":"ok"}`; `/api/lectures` returns 401 and `/docs` is unavailable.
2. Sign in with an invited Google account. Import a YouTube lecture, wait for the syllabus, select one chapter, and generate cards. Check flipping, transcript excerpts, timestamps, topic study, and custom mix. A queued or failed job is not a completed lesson.
3. If YouTube blocks caption retrieval, attach matching SRT/VTT captions. Free online hosting cannot accept the original video; use the local app for that.
4. Check a second invited Google account: it starts empty and cannot access the first account's lecture or job IDs. Sign out; private APIs must return 401. An uninvited account cannot enter.
5. Redeploy the server (discarding its local filesystem). Confirm lessons, cards, sessions, and completed ranges remain available. Interrupted jobs must appear retryable. No private record depends on `/tmp/recall` surviving.

## Connect GitHub Pages

After the live checks pass:

1. Repository **Settings → Pages → Build source: GitHub Actions**.
2. **Settings → Secrets and variables → Actions → Variables**: set `RECALL_APP_URL` to the verified HTTPS backend origin. This URL is public; it contains no secret.
3. **Actions → Publish connected Pages → Run workflow**, branch `main`, `backend_url` equal to that origin.
4. Open Pages, paste a video, select **Proceed to lesson**, sign in, and confirm one lesson is created in your library. Reload during the transition and check it does not create a duplicate.

The workflow checks backend health before replacing the entry page. Subsequent main pushes update connected Pages. Until configured, the entry page retains its honest unconnected notice.

## Operation and backups

The container supervises one API and one worker. A PostgreSQL session advisory lock permits only one active worker across overlapping deployments. A durable ownership token is checked and row-locked in each worker database transaction, so an obsolete worker cannot overwrite successor results. Losing the lease or encountering a database failure terminates the worker and API; the restarted worker recovers interrupted jobs as retryable. Private responses are not cacheable, cookies are Secure/HttpOnly, and sign-out revokes sessions and clears tab study progress.

Supabase stores the durable account registry, account schemas, and session schema. Temporary directories under `/tmp/recall` contain only runtime files and worker heartbeat. In local mode, SQLite, videos, and transcription checkpoints remain under the ignored `data/` directory.

Free hosting is not a backup. Periodically make an encrypted PostgreSQL dump of all `recall_*` schemas using your database connection privately, and keep it outside any public repository. Restore into a dedicated database while both API and worker are stopped. Use the same Google client and verified account subjects; clear restored session rows if reviving unexpired sessions is undesirable. Also back up the local `data/` directory separately if you use the local app.

GitHub's **Hosting checks** use a real disposable PostgreSQL database and a real 512 MB Docker container. They verify encrypted database connections, persistence after completely replacing the container, signed-out denial, queue concurrency, worker ownership, and shutdown on worker failure. Test credentials are fabricated; no Google/OpenAI calls are made. Live sign-in and generation still require the operator steps above.
