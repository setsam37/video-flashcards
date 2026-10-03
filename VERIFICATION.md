# Verification

## Real lecture and provider

The user-supplied [freeCodeCamp System Design course](https://www.youtube.com/watch?v=C842vFY5kRo) was imported through the running API and production worker. It yielded 15 instructor chapters, 3,173 caption segments, and 7 inferred subtopics across a 7,522-second lecture. No cards were generated until Single Server Setup (185–432 seconds) was explicitly selected and Generate was pressed in the browser.

That real provider job succeeded with 8 cards and one visual coverage note. A second real API support check accepted all 8 cards. Manual comparison confirmed the chapter's core points: starting small, shared server components, DNS/request flow, browser/mobile responses, traffic sources, scaling limitations, and takeaways. One answer was shortened to remove an extra phrase not stated explicitly in its cited excerpt. This illustrates why automated model checks are not a guarantee; the supporting transcript remains visible for inspection. The visual note covers the on-screen example that captions did not fully describe.

Every example card's primary timestamp falls inside the selected chapter, every timestamp lies inside its source envelope, and every cited segment ID resolves to the imported transcript. Other chapters have no cards yet. The full lecture syllabus remains available for the learner's next selection.

## Automated checks

- Python suite with live API connection enabled: 59 passed before the final independent review.
- React/Vitest: 13 passed in 5 files.
- TypeScript checking and Vite production build passed.
- FFmpeg created an actual short MP4; ffprobe measured its duration. Audio chunking, timestamp offsets, interruption/retry, rolling captions, and malformed chapter cases are covered in backend tests.
- Local API range requests returned HTTP 206 and the requested bytes, supporting media seeking.
- Origin checks accept the local bound port, reject external origins and malformed ports, and reject untrusted Host headers.
- Hidden PowerShell launcher started the API and worker; stop verifies recorded process executable, creation time, and command before termination. A regression test covers the Windows console-host child process.

The independent review identified two important behavior defects: reloading an older lecture opened the newest import, and partially missing chapter metadata prevented inferred topics in the gaps. Both were reproduced with failing tests and fixed. A setup issue was also fixed so a fresh installation uses its local virtual environment. The final suite passed **62 backend tests (including a real API connection), 14 frontend tests, TypeScript checking, and the production build**. The two-lecture reload fix also passed in the browser, retaining the older lecture's second card and answer side. No critical findings were reported.

One minor accessibility improvement is deferred: Enter on the focusable card area does not flip it. Clicking, Space, and the explicit Flip button work.

The ignored temporary review workspace was retained because automatic approval policy blocked recursive cleanup. Implementation decisions are preserved in `IMPLEMENTATION-NOTES.md`; the app is committed on `feature/video-flashcards` and continues running locally.

## Browser checks

The complete flow was exercised through the supplied browser tools against an isolated fixture server, using the same production routes, worker, persistence, and built interface:

- Import produced chapters and a substantial child topic before any cards existed.
- Selecting the child generated exactly 2 cards with primary times inside its interval; the parent remained partially selected.
- A custom mix flipped to the answer and exposed the correct 330/350-second source URL and transcript.
- Right arrow advanced to card 2 and reset its answer side; Space flipped it. Reload retained card 2 and the answer side.
- A later selected chapter failed deliberately. The completed first chapter's 3 cards survived. Retry finished the remaining chapter, yielding 4 cards.
- Studying one topic included only that topic's card.
- A whole-lecture mix included all 4 generated fixture cards.
- The study layout at 390 pixels wide had a 390-pixel document width and no horizontal overflow. The desktop layout and real lecture workspace were visually inspected.

The Node Playwright runner could not start its worker inside this Windows sandbox (`spawn EPERM`). Its portable test and config are retained for running in a normal terminal; the equivalent browser flow above passed here. Offline fixture checks are distinct from the real lecture/provider checks.

## Limits

The actual uploaded-video Whisper path was implemented and covered with chunk/offset tests; a full user lecture upload has not yet been supplied. The real example used its public captions. Visual frame analysis, extra supporting explanations, spaced repetition, sharing, and exports are outside this first version. Model-based topic extraction and answer checking can make mistakes; timestamped evidence is included for review.
