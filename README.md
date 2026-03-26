#RG Cloud KiCAD

RG Cloud KiCAD is a web platform for browsing, reviewing, and operating on KiCad repositories from the browser. It combines a FastAPI backend, a React/Vite frontend, repository import/sync flows, RBAC-based access control, comments export helpers, and manufacturing/documentation workflows in one workspace.

![KiCAD Prism Home Page](assets/KiCAD-Prism-Login-Page.png)

## Core Capabilities

### Workspace and Repository Management

- Import standalone KiCad repositories or monorepos that contain multiple boards.
- Sync repositories from their remotes without leaving the UI.
- Organize projects into folders with RBAC-aware visibility.
- Search projects by name, display name, description, and parent repo.

<p align="center">
  <img src="assets/KiCAD-Prism-New-Workspace.png" width="49%" alt="Workspace Overview">
  <img src="assets/KiCAD-Prism-Importing-Repo.png" width="49%" alt="Importing Repositories">
</p>

### Project Exploration

- Native schematic and PCB viewing in the browser with cross-probe support.
- 3D board viewing and Interactive HTML BOM integration.
- Markdown README and project docs browsing.
- Design outputs and manufacturing outputs browsing and download.
- Project history, releases, and visual diff support.

<p align="center">
  <img src="assets/KiCAD-Prism-Visualizer-SCH.png" width="49%" alt="Schematic Viewer">
  <img src="assets/KiCAD-Prism-Visualizer-PCB.png" width="49%" alt="PCB Viewer">
</p>

<p align="center">
  <img src="assets/KiCAD-Prism-Visualiser-3DView.png" width="49%" alt="3D Viewer">
  <img src="assets/KiCAD-Prism-Visualizer-ibom.png" width="49%" alt="Interactive BOM">
</p>

### Review and Collaboration

- Comments are stored in SQLite for live collaboration.
- `.comments/comments.json` can be exported for repository-based workflows.
- Per-project helper URLs are exposed to configure KiCad REST comment sources.
- Role-based access control separates viewer, designer, and admin permissions.

<p align="center">
  <img src="assets/KiCAD-Prism-Commenting-Mode.png" width="49%" alt="Commenting Mode">
  <img src="assets/KiCAD-Prism-Comment-Dialog.png" width="49%" alt="Comment Dialog">
</p>

> Integration into KiCAD natively is currently on an experimental custom build of KiCAD v9.99. For now, users can use this platform for tracking comments

### Workflow Automation

- Trigger KiCad workflow jobs from the UI.
- Generate design, manufacturing, and render outputs.
- Browse generated artifacts from the project detail page.

![Workflow Management](assets/KiCAD-Prism-Workflows.png)

## Architecture

- Frontend: React, TypeScript, Vite, Tailwind, shadcn/ui
- Backend: FastAPI, GitPython, Pydantic Settings
- Storage:
  - imported repositories under `data/projects`
  - SSH material under `data/ssh`
  - user accounts, OAuth tokens, project memberships, invites, and access requests in `data/users.db` (SQLite)
  - system role assignments in `.rbac_roles.json`
  - folder metadata in `.folders.json`
  - comments in SQLite plus optional `.comments/comments.json` export
- Runtime split:
  - Docker frontend serves the production bundle on port `8080`
  - backend API serves on port `8000`

## Quick Start

### Docker

```bash
git clone
cd KiCAD-Prism
cp .env.example .env
```

Guest mode (no authentication):

```env
AUTH_ENABLED=false
```

Email/password login:

```env
AUTH_ENABLED=true
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-me-to-a-strong-password
SESSION_SECRET=replace-with-a-long-random-secret
APP_URL=http://localhost:5173
```

Google OAuth login:

```env
AUTH_ENABLED=true
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
SESSION_SECRET=replace-with-a-long-random-secret
BOOTSTRAP_ADMIN_USERS_STR=admin@example.com
SESSION_COOKIE_SECURE=false
```

GitHub OAuth login (requires a GitHub OAuth App):

```env
AUTH_ENABLED=true
GITHUB_CLIENT_ID=your-github-oauth-client-id
GITHUB_CLIENT_SECRET=your-github-oauth-client-secret
GITHUB_ORG_LOGIN=your-github-org
TOKEN_ENCRYPTION_KEY=   # generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
SESSION_SECRET=replace-with-a-long-random-secret
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=change-me-to-a-strong-password
```

Optionally, add the GitHub App for server-side repository access (see [Authentication](#authentication) for setup steps):

```env
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=<base64-encoded-pem>
GITHUB_APP_INSTALLATION_ID=12345678
GITHUB_WEBHOOK_SECRET=<random-hex>
```

Start the stack:

```bash
docker compose up --build -d
```

Open the UI at [http://127.0.0.1:8080](http://127.0.0.1:8080).

Important:
- `SESSION_SECRET` is required whenever auth is effectively enabled.
- `SESSION_COOKIE_SECURE=true` should be used only behind HTTPS.
- Docker Compose reads the root `.env` automatically.

### Local Development

Backend:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs on [http://127.0.0.1:5173](http://127.0.0.1:5173).

By default, local development usually runs without auth because `DEV_MODE=true` and no Google client ID is configured.

## Authentication

RG Cloud KiCAD supports multiple authentication providers. All providers converge on the same HMAC-signed `kicad_prism_session` HttpOnly cookie used for all subsequent API calls.

### Authentication Providers

| Provider | Purpose | Required Variables |
|---|---|---|
| Email / Password | Built-in sign-in, email verification, and password reset | `ADMIN_EMAIL`, `ADMIN_PASSWORD`, SMTP settings |
| Google OAuth | Sign in with a Google account | `GOOGLE_CLIENT_ID` |
| GitHub OAuth App | Sign in with a GitHub account | `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` |

> **GitHub App vs. GitHub OAuth App — these are two distinct GitHub products with different purposes.**
> The **GitHub OAuth App** lets _users_ sign in with their GitHub identity.
> The **GitHub App** is a server-side integration that lets the _application itself_ call the GitHub API (browse repos, sync, handle webhooks). They can be configured independently.

Auth is **effectively enabled** when all three are true: `AUTH_ENABLED=true`, `DEV_MODE=false`, and at least one provider is configured. Set `DEV_MODE=true` or `AUTH_ENABLED=false` to bypass authentication during development.

### System Roles (RBAC)

| Role | Permissions |
|---|---|
| `viewer` | Read-only; browse projects they have access to |
| `designer` | Import, sync, comments, folder/project mutations, and workflows |
| `admin` | All of the above plus settings and system role management |

System roles are stored in `.rbac_roles.json` (override the path with `ROLE_STORE_PATH`).

**Auto-assignment rules (evaluated on each login):**
1. Accounts in `ADMIN_EMAIL` or `BOOTSTRAP_ADMIN_USERS_STR` are permanently resolved as `admin`.
2. Users whose email domain is in `ALLOWED_EMAIL_DOMAINS_STR` are automatically approved as `viewer`.
3. GitHub OAuth users who are members of `GITHUB_ORG_LOGIN` are automatically promoted to `designer`.
4. All other new users are placed in a **pending queue** until an admin approves them.

### Bootstrap Admin

On first startup the server automatically creates the account defined by `ADMIN_EMAIL` + `ADMIN_PASSWORD` with full admin rights and a verified email address. After the first run, changing `ADMIN_PASSWORD` in `.env` does **not** update the stored password — use the forgot-password email flow to change it.

### GitHub OAuth App (User Login)

The GitHub OAuth App enables users to sign in with their GitHub identity. During login:
1. The user is redirected to GitHub for authorization.
2. On callback, RG Cloud KiCAD stores the user's GitHub access token **encrypted** in the database — `TOKEN_ENCRYPTION_KEY` must be set for this.
3. If `GITHUB_ORG_LOGIN` is set, only members of that organization are allowed in (non-members receive a 403).
4. GitHub org members are automatically upgraded to the `designer` system role.

Create a GitHub OAuth App at: Organization → Settings → Developer settings → OAuth Apps → New OAuth App. Set the callback URL to `{APP_URL}/api/auth/github/callback`.

### GitHub App (Server-Side API Access)

The GitHub App is a separate GitHub product that gives the RG Cloud KiCAD server its own identity for GitHub API calls. It is used for:
- Browsing organization repositories
- Cloning and syncing projects
- Processing webhook events (`push`, `create`, issues, commit comments)

The GitHub App generates short-lived installation access tokens (cached in memory, refreshed automatically 5 minutes before expiry) and does not act on behalf of any individual user.

Setup steps:
1. Create a GitHub App: Organization → Settings → Developer settings → GitHub Apps → New GitHub App.
2. Required permissions: Contents (Read), Administration (Read), Issues (Read), Pull requests (Read).
3. Subscribe to events: Create, Commit comments, Issues, Push.
4. Set the Webhook URL to `{APP_URL}/api/github/webhook`.
5. Install the App on your organization and copy the Installation ID from the install confirmation URL.
6. Generate and download a private key from the App settings page.

### Email / SMTP

SMTP is required for:
- Email address verification for new email/password registrations
- Password reset links
- Admin notifications when a new user registers without domain auto-approval

SMTP is **optional**: without it the bootstrap admin and manually-approved users still work. Verification and notification emails are silently skipped when `SMTP_HOST` is not set.

Generate the `TOKEN_ENCRYPTION_KEY` for storing GitHub access tokens:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Project Access Control

Project-level access control is independent of system RBAC. Each project has a **visibility** setting, and users can hold a project-specific role that supplements their system role.

### Project Visibility

| Visibility | Access |
|---|---|
| `public` | Readable by any authenticated user with `designer` or higher system role |
| `private` | Only explicit project members can access |
| `hidden` | Invisible to everyone except explicit members; even system `admin` provides no bypass |

### Project Roles

| Role | Permissions |
|---|---|
| `viewer` | Browse project files, schematics, BOM, and history |
| `manager` | Manage members, approve/deny access requests, send invites |
| `admin` | All of the above plus updating project visibility and settings |

Bootstrap admins and system-level `admin` users always receive implicit `admin` project access on non-hidden projects.

### Access Flows
- **Self-join**: Users with `designer`+ system role can self-join any public project.
- **Access request**: Any authenticated user can request access; project managers/admins approve or deny, and the requester is notified by email.
- **Invite by email**: Project managers/admins send time-limited email invites. Invites can be accepted or declined and are automatically revoked when a replacement invite is sent.
- **Direct add**: Project managers/admins can directly add or update members by email address.

## Project Documentation

- Deployment and hosting: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)
- Repository layout expectations: [docs/KICAD-PRJ-REPO-STRUCTURE.md](./docs/KICAD-PRJ-REPO-STRUCTURE.md)
- Path mapping and `.prism.json`: [docs/PATH-MAPPING.md](./docs/PATH-MAPPING.md)
- Display names and project metadata: [docs/CUSTOM_PROJECT_NAMES.md](./docs/CUSTOM_PROJECT_NAMES.md)
- Comments export and REST helpers: [docs/COMMENTS-COLLAB-UPDATES.md](./docs/COMMENTS-COLLAB-UPDATES.md)
- Workspace behavior notes: [docs/WORKSPACE_UX_IMPROVEMENTS.md](./docs/WORKSPACE_UX_IMPROVEMENTS.md)
- Visualizer vendor sync notes: [docs/ECAD_VIEWER_SYNC_NOTES.md](./docs/ECAD_VIEWER_SYNC_NOTES.md)

## Repository Layout

```text
KiCAD-Prism/
├── backend/            # FastAPI backend
├── frontend/           # React frontend
├── docs/               # Project documentation
├── assets/             # Screenshots and media for docs
└── data/               # Runtime data in local/Docker use
```

## Acknowledgements

- [ecad-viewer](https://github.com/Huaqiu-Electronics/ecad-viewer)
- [KiCanvas](https://kicanvas.org)
- [Interactive HTML BOM](https://github.com/quindorian/Sublime-iBOM-Plugin)
- [Three.js](https://threejs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)

## License

This project is licensed under the Apache-2.0 License.
