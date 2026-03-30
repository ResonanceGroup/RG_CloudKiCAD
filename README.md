#RG Cloud KiCAD

> **🐳 Unified Docker Image** • Single `.env` file • One command deployment • Dev = Production workflow

RG Cloud KiCAD is a web platform for browsing, reviewing, and operating on KiCad repositories from the browser. It combines a FastAPI backend, a React/Vite frontend, repository import/sync flows, RBAC-based access control, comments export helpers, and manufacturing/documentation workflows in one workspace.

**Key Features**:
- Single Docker image with both frontend and backend
- One `.env` file for all configuration
- Identical development and production workflow
- Multi-architecture support (amd64/arm64)
- Includes KiCAD 9 with Python bindings

![KiCAD Prism Home Page](assets/KiCAD-Prism-Login-Page.png)

## Table of Contents

- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Authentication](#authentication)
- [Project Access Control](#project-access-control)
- [Documentation](#documentation)
- [Repository Layout](#repository-layout)
- [Acknowledgements](#acknowledgements)
- [License](#license)

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

### Unified Container Design

KiCAD Prism uses a **single Docker image** containing both frontend and backend services. Both run in the same container, managed by supervisor:

- **Frontend** (nginx on port 80): Serves the React build and proxies API requests
- **Backend** (uvicorn on port 8000): FastAPI application handling all business logic 
- **Communication**: nginx ➜ `localhost:8000` ➜ FastAPI (internal to container)
- **External access**: Single port configurable via `PORT` in `.env` (default: 8080)

### Technology Stack
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui
- **Backend**: FastAPI, Python 3, GitPython, Pydantic Settings, SQLAlchemy
- **Database**: SQLite (users, OAuth tokens, memberships, invites, access requests)  
- **Container**: Ubuntu-based with KiCAD 9, nginx, Python, supervisor
- **Deployment**: Single image via docker-compose (amd64/arm64 support)

### Storage (Persisted)
- **Project repositories**: `data/projects/` (organized by type)
- **SSH keys**: `data/ssh/` (for Git operations)
- **User database**: `data/users.db` (SQLite)
- **System roles**: `.rbac_roles.json` in projects root
- **Folder metadata**: `.folders.json` in projects root
- **Comments**: SQLite with optional `.comments/comments.json` export

### Why One Container?

**Simplicity**: One image, one command, one `.env` file  
**Consistency**: Development workflow identical to production  
**No networking complexity**: Services communicate via localhost  
**Easier deployment**: Single container to manage and monitor

## Quick Start

> **📖 Detailed guide: [docs/QUICKSTART.md](docs/QUICKSTART.md)**

### 1. Setup

```bash
# Clone repository
git clone <repository-url>
cd KiCAD-Prism

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings
```

### 2. Configure `.env`

**Minimum required settings**:
```env
# Port (where to access the app)
PORT=8080

# Application URL (for emails and OAuth callbacks)
APP_URL=http://localhost:8080

# Admin account
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password

# Session security
SESSION_SECRET=generate-a-random-secret

# Authentication
AUTH_ENABLED=true
```

**Optional GitHub OAuth** (recommended):
```env
GITHUB_CLIENT_ID=your-oauth-app-client-id
GITHUB_CLIENT_SECRET=your-oauth-app-secret
GITHUB_ORG_LOGIN=your-organization
TOKEN_ENCRYPTION_KEY=generate-with-python

# GitHub App (for repository operations)
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=base64-encoded-private-key
GITHUB_APP_INSTALLATION_ID=12345678
GITHUB_WEBHOOK_SECRET=random-hex-string
```

See `.env.example` for all options.

### 3. Start the Application

```bash
# Build and start (first time)
docker-compose up -d --build

# View logs
docker-compose logs -f

# Access the app
# Open http://localhost:8080 in your browser
```

### 4. Common Commands

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart after config changes
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### That's It!

Development and production use the same workflow. No separate dev setup needed.

## Configuration

### Single `.env` File

All configuration is in one file: `.env` at the project root.

**Key variables**:

| Variable | Purpose | Example |
|----------|---------|---------|  
| `PORT` | Application port | `8080` |
| `APP_URL` | Public URL | `https://prism.yourcompany.com` |
| `ADMIN_EMAIL` | Bootstrap admin | `admin@example.com` |
| `ADMIN_PASSWORD` | Admin password | `SecurePassword123!` |
| `SESSION_SECRET` | Cookie signing key | (random string) |
| `AUTH_ENABLED` | Enable authentication | `true` |
| `GITHUB_CLIENT_ID` | GitHub OAuth App | (from GitHub) |
| `GITHUB_APP_ID` | GitHub App | (from GitHub) |
| `SMTP_HOST` | Email server | `mail.yourcompany.com` |

See `.env.example` for complete list with documentation.

### Generate Secrets

```bash
# SESSION_SECRET
openssl rand -base64 32

# TOKEN_ENCRYPTION_KEY (for GitHub OAuth)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# GITHUB_WEBHOOK_SECRET
python -c "import secrets; print(secrets.token_hex(32))"
```

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

## Documentation

### Getting Started
- **Quick Start Guide**: [docs/QUICKSTART.md](./docs/QUICKSTART.md) - One-page setup guide
- **Production deployment**: [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) - Hosting and production best practices

### Project Configuration  
- **Repository structure**: [docs/KICAD-PRJ-REPO-STRUCTURE.md](./docs/KICAD-PRJ-REPO-STRUCTURE.md) - Expected repository layout
- **Path mapping**: [docs/PATH-MAPPING.md](./docs/PATH-MAPPING.md) - `.prism.json` configuration
- **Custom project names**: [docs/CUSTOM_PROJECT_NAMES.md](./docs/CUSTOM_PROJECT_NAMES.md) - Display names and metadata

### Features & Collaboration
- **Comments & collaboration**: [docs/COMMENTS-COLLAB-UPDATES.md](./docs/COMMENTS-COLLAB-UPDATES.md) - Export and REST helpers
- **Workspace UX**: [docs/WORKSPACE_UX_IMPROVEMENTS.md](./docs/WORKSPACE_UX_IMPROVEMENTS.md) - UI behavior notes
- **Visualizer sync**: [docs/ECAD_VIEWER_SYNC_NOTES.md](./docs/ECAD_VIEWER_SYNC_NOTES.md) - Vendor component updates

## Repository Layout

```text
KiCAD-Prism/
├── Dockerfile             # Unified multi-stage container (frontend + backend)
├── .dockerignore          # Docker build exclusions
├── docker-compose.yml     # Single unified service
├── .env                   # Single configuration file (all settings)
├── .env.example           # Configuration template
├── docker/                # Container configuration
│   ├── supervisord.conf  # Process manager (nginx + uvicorn)
│   └── nginx.conf        # Nginx proxy configuration
├── backend/               # FastAPI backend
│   ├── app/              # Application code
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Configuration, security, RBAC
│   │   ├── db/           # Database models
│   │   ├── schemas/      # JSON schemas
│   │   └── services/     # Business logic
│   └── requirements.txt  # Python dependencies
├── frontend/              # React + Vite frontend
│   ├── src/              # React components and pages
│   ├── public/           # Static assets and viewer libraries
│   └── package.json      # Node dependencies
├── docs/                  # Project documentation
│   ├── QUICKSTART.md     # One-page setup guide
│   ├── DEPLOYMENT.md     # Production hosting guide
│   └── *.md              # Feature and configuration docs
├── assets/                # Screenshots and media
└── data/                  # Runtime data (Docker volumes)
    ├── projects/         # Imported KiCAD repositories
    ├── ssh/              # SSH keys for Git
    └── users.db          # SQLite user database
```

### Key Files
- **`Dockerfile`**: Multi-stage build that creates frontend bundle, then combines with backend in unified image
- **`.env`**: Single source of truth for all configuration (port, credentials, features)
- **`docker-compose.yml`**: Runs the unified container with volume mounts
- **`docker/supervisord.conf`**: Manages nginx (frontend) and uvicorn (backend) processes

## Acknowledgements

- [ecad-viewer](https://github.com/Huaqiu-Electronics/ecad-viewer)
- [KiCanvas](https://kicanvas.org)
- [Interactive HTML BOM](https://github.com/quindorian/Sublime-iBOM-Plugin)
- [Three.js](https://threejs.org/)
- [FastAPI](https://fastapi.tiangolo.com/)

## License

This project is licensed under the Apache-2.0 License.
