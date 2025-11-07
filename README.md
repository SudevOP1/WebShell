# WebShell

### Web "SSH" Terminal (PTY) + Job Runner
**Timebox**: 6–8 hours<br>
**Goal**: Build a web app with an **in-browser terminal** connected to a **server-side pseudo-TTY (PTY)** to run commands inside a jailed environment (no real remote SSH). Add a simple job runner UI on top.<br>

### Must-haves
- **Frontend**: Next.js/React. Terminal UI using xterm.js (or similar). Live streaming via
WebSockets/SSE; no polling.
- **Backend**: Python FastAPI (preferred) or Node/Express. Use pty / ptyprocess (py) or
node-pty to spawn a shell in a chroot/container/jail; enforce a command allowlist
(e.g., ls, echo, cat, grep).
- **Security guardrails**:
    - Prevent file writes and network egress (mount read-only FS or minimal
container).
    - Timeouts + CPU/mem limits.
    - Command audit log with {userId, cmd, exitCode, duration} to a DB
(SQLite/Postgres).
- **Jobs**: A "Saved Jobs" panel to store sequences of allowed commands and replay
them with step-by-step output.
- **Auth**: Email magic link or GitHub OAuth; roles: viewer (read logs), operator (run).
- **Observability**: Structured logs (JSON) and a /healthz endpoint.

### Deliverables
- Repo with docker-compose that boots the web, API, and a jailed runner.
- Short **Loom video (≤4 min)**: demo terminal, job replay, logs, failure case.
- README with threat model (what you blocked, what you didn’t), and a 1-page
"Design Choices".

### Stretch (optional)
- RBAC policies per command group.
- Downloadable **session transcript** (ANSI stripped).
- Simple rate limits & CSRF/Origin protections.