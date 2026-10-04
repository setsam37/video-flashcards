# Recall

A personal, local app that turns a lecture into a chapter syllabus and flashcards based on what the lecture teaches.

## GitHub Pages

The public entry page is published at [setsam37.github.io/video-flashcards](https://setsam37.github.io/video-flashcards/). GitHub Pages serves static files and cannot run this app's Python processing worker. It keeps an unconnected notice until a server is configured. The Render setup supports Google sign-in and a separate private library per invited account. See [HOSTING.md](HOSTING.md) for setup and live verification; source preparation alone does not deploy a server.

Build the Pages entry screen with `npm --prefix web run build:pages`. This writes `web/dist-pages` with relative asset paths suitable for a project Pages URL. Only those generated files belong in the Pages deployment. The current site uses the `gh-pages` branch; the connected-site workflow publishes through GitHub Actions. The normal build still writes `web/dist` and serves the full local or hosted app. The Pages build receives only `VITE_APP_URL`, the public server origin, when processing is live.

## Open your app

On this computer, the Python environment, web dependencies, FFmpeg paths, API key, and production build are already configured. From this folder in PowerShell:

```powershell
./scripts/start.ps1
```

Open **http://127.0.0.1:8000**. To stop the service and worker:

```powershell
./scripts/stop.ps1
```

The launcher starts hidden processes and writes logs to `data/logs`. It records executable paths, process creation times, and application roles; stopping verifies both process identity and commands. If a record already exists, stop before restarting. `start.ps1 -Dev` also starts the development UI on port 5173. `start.ps1 -Build` rebuilds the production interface.

## Study a lecture

1. Paste a YouTube link or upload an MP4/WebM video. The app retrieves captions or transcribes uploaded audio, then prepares the syllabus. No cards are generated at this stage.
2. Select whole chapters or substantial subtopics. Selecting a parent includes its entire chapter; selecting children individually includes only those children.
3. Click **Generate flashcards**. Each card has a lecture excerpt and timestamp. Coverage notes identify visual material or points that could not produce a supported answer.
4. Choose **Mix the lecture**, **Custom mix**, or **Study one topic**. A lecture mix includes material already generated. Click a card or use Space to flip; arrows move between cards.
5. On the answer, use **Watch this explanation** or expand the supporting transcript. Reloading the same browser tab resumes the current card and answer side.

Completed chapters persist even if a later generation request fails. Retry continues remaining work. Regeneration replaces selected material only after every selected section succeeds, preserving the previous deck on failure.

## Verified example

The supplied freeCodeCamp System Design video (`C842vFY5kRo`) imported through the real app with 15 instructor chapters, 3,173 timestamped caption segments, and 7 inferred subtopics. Real OpenAI generation was run for **Single Server Setup (3:05–7:12)**. The initial run produced 8 cards and one visual coverage note. See `VERIFICATION.md` for the final checks and any later fixes.

## Configure another computer

Use Python 3.12+, Node 24+, and FFmpeg/ffprobe. Create a virtual environment, install the locked Python requirements and the web dependencies, then build:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r backend/requirements.lock
npm --prefix web ci
npm --prefix web run build
Copy-Item .env.example .env
```

In `.env`, set `OPENAI_API_KEY`, `FFMPEG_PATH`, and `FFPROBE_PATH`. The latter two should be full executable paths or names on PATH. The optional `OPENAI_TEXT_MODEL` defaults to `gpt-4.1-mini-2025-04-14`. Use an account with access to that model and Whisper transcription.

The launcher uses `scripts/runtime.json` when configured, then prefers `.venv/Scripts/python.exe`, then Python from PATH. Node uses its configured path or PATH. A local runtime file can specify `python` and `node` executable paths. On another computer, remove or update that ignored file. The current computer's runtime and downloaded executables are in the sibling `../../work/video-flashcards-runtime` folder; keep that folder when using the configured launcher here.

## Data and provider use

The key stays in the ignored backend `.env` locally or in server environment settings when hosted, and is never sent to the browser. Local lessons and videos remain under the ignored `data` folder. Free hosted lessons, transcripts, cards, jobs, and sessions persist in a private Supabase PostgreSQL database; the Render server uses no paid disk. Hosted import supports YouTube/captions; original video upload/transcription is local. Back up local data and the hosted database separately. Provider calls incur charges on your OpenAI account: uploaded audio goes to Whisper, and transcript excerpts go to the text model for syllabus, point extraction, cards, and evidence checking. Text calls use `store=False`. Hosted mode supports invited Google accounts with separate libraries; there is no user billing or sharing feature.

This version uses audio/captions rather than video frames. Captions can contain errors, and model evidence checks are imperfect; supporting excerpts let you inspect an answer. Visual-only diagrams and code are flagged when identified. English YouTube captions are preferred. If YouTube captions are unavailable, attach SRT/VTT captions or upload the video. If metadata itself fails, upload the video or retry later. A timestamped caption file must belong to the original lecture.

## Development verification

```powershell
$env:PYTHONPATH = 'backend'
python -m pytest backend/tests -q
npm --prefix web test -- --run
npm --prefix web run build
```

PostgreSQL integration checks run when `TEST_DATABASE_URL` points to a disposable test database. GitHub Actions supplies PostgreSQL 17 and also replaces the complete Docker container to verify data survives free-server filesystem loss. Do not point integration tests at a real library database.

Live checks are explicitly opt-in and consume API credits:

```powershell
$env:RUN_LIVE_TESTS = '1'
python -m pytest backend/tests/test_live_provider.py -q
python scripts/live_check.py --lecture-id YOUR_ID --interval 185 432
```

For the portable browser test, install Playwright Chromium (`npx --prefix web playwright install chromium`), start the isolated test server, then run the E2E test in another terminal:

```powershell
$env:PYTHONPATH = 'backend'
python backend/tests/e2e_server.py
# another terminal
npm --prefix web run test:e2e
```

That server is defined exclusively in `backend/tests`; production cannot enable its fixture provider. It uses an isolated temporary database and clearly labeled fixture content. The test covers selective generation, source timestamps, flip, keyboard navigation, reload, custom/topic mixes, partial failure, and retry.

Inside the Codex Windows sandbox, Node cannot spawn the Playwright worker or npm command shell. Verification here uses direct Node CLI entrypoints and the provided browser tools. This restriction does not indicate a failure of the app. The development-only runtime import handles Vite's optional network-drive discovery; it is not part of the delivered web build.
