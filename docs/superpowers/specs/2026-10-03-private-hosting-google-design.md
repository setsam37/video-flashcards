# Private Recall hosting with Google sign-in

## Intended outcome

Recall provides a separate private study library for each invited Google account. The user wants a simple first screen: a large box to paste a YouTube video, a Proceed to lesson button, and the existing syllabus and flip-card study experience after processing. Google sign-in replaces a separate app password. The same account can open its library from any device or IP address. This revises the original single-owner scope following the user's request that each email access its own data.

The chosen direction is GitHub Pages first, then Render. Pages presents the public entry screen. Render hosts the protected working application and processing service. This document describes the proposed changes; these changes are not implemented or deployed yet.

## Hosting approach

Use one Docker-based Render service with the FastAPI application, built React interface, processing worker, FFmpeg, and ffprobe. The API and worker run as separate supervised processes in the same container and share a persistent disk mounted at `/var/data`. Keep SQLite and the existing queue; this is a single-instance personal app.

A GitHub Pages entry screen is separate from the Render interface. Keeping the private interface and its API on the same Render origin permits normal protected video playback and avoids depending on third-party cookies between github.io and onrender.com. A single Render-hosted site would require fewer moving parts, but the proposed arrangement preserves the user's requested GitHub Pages entry page. A VPS is a portable alternative supported by the Docker image, with more server maintenance required.

Render manages the public HTTPS endpoint. Its platform-assigned hostname is sufficient initially; buying a custom domain is unnecessary. The existing Windows launcher and local library remain usable.

## Entry and lesson flow

1. The Pages screen shows Recall branding, a large empty YouTube URL input, and Proceed to lesson. It is usable on mobile and with a keyboard. The current example URL becomes a placeholder or explicit example rather than a prefilled submission.
2. The screen validates supported YouTube URLs and hands the requested video to the configured HTTPS Render application. It stores no API keys, OAuth client secrets, private library, or account identifiers.
3. Render presents Sign in with Google when the visitor has no valid app session. The requested video is retained through sign-in using bounded temporary state.
4. After successful sign-in, the app imports the requested lecture into that account's library. Video preparation uses the existing worker. Visiting without a video opens the account's library or the same simple import screen.
5. Retrying or reloading the sign-in transition must not enqueue the same handoff twice. Invalid URLs, cancelled sign-in, rejected accounts, and temporary processing failures show actionable messages without exposing internal errors.
6. Uploaded MP4/WebM files remain supported in the Render app after sign-in. The Pages entry screen does not upload or proxy video files. Syllabus selection, selective generation, custom mixes, and flip-card study retain their existing behavior.

The Pages deployment must explain that processing is unavailable until the backend is configured; no fixture or simulated generation may be presented as a completed real lesson.

## Google identity and access

Use Google's OpenID Connect authorization-code server flow through a maintained OAuth/OIDC library. Request only `openid email`. Validate OAuth state, nonce, token signature, issuer, audience, expiration, and verified email before granting access. Bind temporary sign-in state to the initiating browser, expire it after 10 minutes, and consume it once. Use PKCE where supported by the selected library.

Configure invited Google emails on the server. Treat each as an exact account address after case normalization, never as a suffix/domain match. Only verified invited accounts may enter by default. Public signup is available as an explicit server setting, but remains disabled until the user chooses it because processing uses the operator's OpenAI key. Google `sub` identifies the authenticated account; a hash of it names a separate account directory containing its SQLite library, uploads, and processing checkpoints. Every API request uses the verified session's workspace, never a browser-supplied email/account ID. The single worker scans these workspaces and handles each queue with its own paths. Libraries are not shared.

After sign-in, issue an opaque random app session cookie and persist only its digest, identity, and expiration in SQLite. Sessions expire after 24 hours. Cookies are HttpOnly, Secure in hosted mode, SameSite=Lax, and scoped to the Render application. Do not place identity tokens, access tokens, or app session tokens in localStorage, query strings, frontend build variables, or logs. Discard Google tokens after validating identity; do not request offline access or retain refresh tokens.

Protect every private API route, uploaded media route, and library response. Public routes are limited to the entry/login page, needed static assets, login start/callback, constrained handoff, session status, and a minimal health response. Public session status discloses only that sign-in is required; account information requires authentication. Sign out revokes the server-side session and expires its cookie. Recheck invitations on authenticated requests so removing an account removes prior access.

Require CSRF protection on state-changing authenticated requests, including logout and import. Allow only the configured application origin, preserve strict Host checks, and validate redirects against local app paths. The Pages handoff is a constrained entry route, not general cross-origin permission to private APIs. Unauthenticated requests must be rejected before video files are processed.

## Configuration and operating behavior

Hosted mode requires a configured HTTPS public application URL, Google client ID and secret, owner email, session signing secret, and OpenAI key. Missing authentication settings stop hosted startup rather than allowing public access. Local mode remains bound to loopback and can retain its existing authentication-free behavior for the owner.

Put all credentials in Render secret environment variables. `.env` remains ignored. The Docker build context excludes `.env`, local data, runtime settings, Git metadata, and scratch files; secrets are never build arguments or copied image assets. The Pages build receives only the public Render URL.

Set the shared application data directory and large-upload temporary directory beneath the persistent disk. Disk size and upload limits are documented together. For an initial personal deployment, propose a 10 GB disk and a 1 GB per-upload limit; the original local 4 GB limit remains available through configuration. Confirm the actual paid service size and price before provisioning.

The container listens on the host-provided PORT at 0.0.0.0, starts exactly one processing worker, forwards shutdown signals, and exits if either long-running process fails. Interrupted jobs retain the existing retryable behavior and saved progress. Health checks must reflect availability of the API, database, and worker without disclosing configuration or credentials.

Document safe SQLite/media backups and restoration. Persistent storage survives routine restarts and redeploys, but is not itself a backup. Moving the existing local library online is a separate explicit action; the initial hosted library starts empty unless the user asks to transfer it.

## Delivery and checks

Deliver the simple entry interface, Google authentication, hosted configuration, Docker image definition, Render deployment template, GitHub Pages workflow, setup instructions, and regression tests. Push reviewed source changes to the existing GitHub repository, preserving its current visibility.

Verify the entry screen and transition on desktop/mobile; signed-out API/media denial; owner sign-in; other-account denial; malformed, expired, replayed, or tampered OAuth/session state; logout revocation; CSRF and Host/origin enforcement; one-time lecture handoff; processing and study flow; worker failure/shutdown; disk persistence across restart; and exclusion of secrets from source, build assets, and image context. Run the existing backend/frontend suites and production build.

Test OAuth logic with isolated provider responses, then perform a real owner login only after real Google credentials and the callback URL are configured. Separately verify the built Docker container and the deployed public endpoints before claiming deployment complete. If Docker is unavailable locally, report that limitation and use a supported build environment; static file checks alone do not verify a container.

## User setup required for live deployment

The user must provide the allowed Google email and configure a Google Cloud Web application OAuth client. Register the exact Render callback URL, configure the consent screen, and enter credentials privately in server settings. A Render account with access to the GitHub repository and the chosen paid disk/service is required. These account and billing steps are distinct from preparing the source code.

The user made the source repository public before the entry page was deployed. Keep that visibility and the existing Pages URL; keep all credentials, private email configuration, and library data out of Git history and Pages assets.

## Sources checked

- [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect): server sign-in, client credentials, exact redirect URI, state/nonce, and identity validation.
- [Render persistent disks](https://render.com/docs/disks): persistence under the mount path, one service instance, and restart/deploy limitations.
- [Render Docker](https://render.com/docs/docker): Docker builds, secrets, and runtime environment configuration.
- [GitHub Pages availability](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages): static hosting and repository/plan eligibility.
