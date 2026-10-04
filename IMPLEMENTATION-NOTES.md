# Implementation decisions and review

Ruling: Fresh project repository on feature/video-flashcards provides isolation — no existing checkout to protect — cost if wrong: relocate the app.
Ruling: Use native Python ledger/brief helpers because Git Bash cannot create signal pipes in this Windows sandbox — preserve the same plan identity and per-task records — cost if wrong: bookkeeping may need reconciliation.
Ruling: Development venv temp directories inherit workspace permissions because Python mode 0700 drops sandbox access — shim limited to this local development environment — cost if wrong: remove shim before distribution.
Task 4: Ruling: Preserve valid chapter end times and infer gaps rather than extending chapters to the next start — the spec preserves instructor boundaries — cost if wrong: revise gap labeling.
Task 5: Ruling: validate_candidate receives lecture_id and nodes as keyword arguments — its promised Card return requires source identity and topic assignment — cost if wrong: update helper callers.
Task 6: Ruling: Regeneration stages every selected unit before one atomic replacement; new generation commits topics independently — preserves old decks on replacement failure and allows partial new results — cost if wrong: failed regeneration repeats model work.
Task 7: Ruling: Run Node CLI entrypoints directly and handle the optional failed Vite network-drive query in a development-only shim — this sandbox blocks command-shell spawning — cost if wrong: mapped-drive projects need another runtime; this project uses a local drive.
Task 9: Ruling: Run the same browser flow with Python Playwright because Node Playwright cannot spawn its worker in this sandbox — browser assertions remain real and the portable TypeScript test is retained — cost if wrong: harness differences may hide a Node-only test-runner issue.
Task 9: Ruling: Browser checks run through the provided CUA Playwright interface; the earlier Python harness choice is superseded by the browser-tool requirement — retain the portable TypeScript E2E test — cost if wrong: scripted checks need a normal Windows terminal to run.
Task 9: Ruling: Shorten one live example answer to its explicitly cited facts after manual audit — the model accepted an uncited extra phrase — cost if wrong: the example loses optional detail.
Final review: fresh independent reviewer, gpt-6-astra; no Critical, two Important and two Minor; Declined to judge: none.
Final: Ruling: Re-grade fresh-install runtime selection as Important — following the promised setup instructions must launch the installed dependencies — cost if wrong: an extra small runtime-selection helper.
Final: fixed older-lecture reload — reload restores the active older lecture and its current answer RED→GREEN, suite 14/14 frontend and 62/62 backend; also verified in browser.
Final: fixed inference within missing chapter intervals — test_partial_chapters_infer_topics_in_uncovered_gap_without_changing_instructor_bounds RED→GREEN, suite 62/62 backend and 14/14 frontend.
Final: fixed fresh-install runtime selection — test_fresh_setup_launcher_uses_the_created_virtual_environment and explicit runtime precedence RED→GREEN, suite 62/62 backend and 14/14 frontend.
Final: minor (deferred): Enter does not activate the card hit area; click, Space, and the Flip button work.
Final: Ruling: Keep the standalone app on feature/video-flashcards — no existing base branch or remote requires integration, and the user authorized completing the local app — cost if wrong: perform a later merge or push when requested.
Final: Ruling: Retain the ignored review workspace after automatic approval policy blocked recursive cleanup — no app functionality depends on deleting those records — cost if wrong: a small amount of extra scratch storage.

## Free backend preparation — October 4, 2026

- Proceeded with design choices and inline implementation under the user's explicit authorization to proceed and choose the most cost-efficient free option. Cost if wrong: the user may prefer another provider; source changes are reversible.
- Used the existing nested repository on `feature/free-backend`; the native worktree tool could not target this repository in the projectless chat. Cost if wrong: checkout changes are visible locally; ignored local data is preserved.
- Added one persistent PostgreSQL session lock and a durable ownership token to prevent overlapping deployments from recovering or overwriting another worker's jobs. Cost: one database connection.
- Preserved the SQLite/disk container check as optional compatibility coverage; the default CI runs the new free PostgreSQL container check. Cost: one additional script.
- The SQL adapter supports application-owned queries. A future query containing literal placeholder punctuation needs an adapter extension and tests.
- Online original-video storage is excluded to fit free hosting; MP4/WebM uploads and transcription remain local. Cost: users must use the local app for those imports.
- Live Supabase pooler, Google sign-in, and provider processing require private credentials and remain deployment gates. Cost if wrong: fixtures may miss a live integration issue. Pages stays unconnected until live checks pass.
- Integrated verified source into the existing `main` deployment branch under the user's GitHub publishing and proceed authorization. Cost if wrong: the source commit can be reverted; Pages remains gated and no paid service is created.

Independent review: one fresh whole-branch reviewer; no Critical issues. Both Important findings were reproduced with failing tests and fixed: obsolete-worker writes are fenced in each database transaction, and database failures exit the worker so interrupted jobs can be recovered after restart. The full CI suite and real free-container check passed afterward. No second review pass was requested.

Minor deferrals: an optional forbidden video attached to a caption request can spool up to the 21 MB request cap before rejection (the dedicated video-upload route rejects before parsing); `sslmode=require` encrypts without verifying server identity, while `verify-full` with the provider CA is documented as preferred hardening.
