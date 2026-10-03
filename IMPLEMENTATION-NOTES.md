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
