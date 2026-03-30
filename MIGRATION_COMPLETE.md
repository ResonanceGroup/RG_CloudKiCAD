# Docker Migration Complete

## Summary

KiCAD Prism has been migrated to a **unified single-container Docker architecture**. This simplifies deployment, development, and maintenance by consolidating both frontend and backend services into one Docker image with a single `.env` configuration file.

## What Changed

### Architecture Transformation

**Before:**
- 2 separate Docker containers (frontend, backend)
- 3 separate .env files (root, backend, frontend)
- Complex networking between containers
- Separate Dockerfiles for each service

**After:**
- 1 unified Docker container with both services
- 1 `.env` file at project root
- Services communicate via localhost
- Single multi-stage Dockerfile
- Identical workflow for development and production

### Files Created

1. **`Dockerfile`** (root)
   - Multi-stage build: Node builder stage + unified final image
   - Supports multi-architecture (amd64/arm64)
   - Contains both frontend (nginx) and backend (uvicorn)

2. **`docker/supervisord.conf`**
   - Manages both nginx and uvicorn processes
   - Automatic restart on failures
   - Coordinated startup sequence

3. **`docker/nginx.conf`**
   - Serves React frontend on port 80
   - Proxies `/api/` requests to `localhost:8000`
   - Single-container communication

4. **`.dockerignore`** (root)
   - Excludes unnecessary files from Docker build
   - Optimizes build performance

5. **`docs/QUICKSTART.md`**
   - One-page setup guide
   - Simple 4-step process
   - Common commands reference

### Files Modified

1. **`docker-compose.yml`**
   - Changed from 2 services to 1 service (`app`)
   - Single port mapping: `${PORT:-8080}:80`
   - All environment variables explicitly listed
   - Health checks for both frontend and backend

2. **`.env`** (root)
   - Now contains all configuration
   - Simplified to single `PORT` variable
   - Your Resonance Group credentials preserved

3. **`.env.example`** (root)
   - Simplified to show only essential variables
   - Removed separate BACKEND_PORT/FRONTEND_PORT
   - Added PORT variable with default 8080

4. **`README.md`**
   - Updated Quick Start section (removed local dev)
   - Updated Architecture section (explained unified design)
   - Updated Repository Layout (shows new structure)
   - Updated Configuration section (single .env approach)
   - Removed references to deleted documentation

### Files Deleted

1. **Docker configurations:**
   - `backend/Dockerfile` (replaced by root Dockerfile)
   - `frontend/Dockerfile` (replaced by root Dockerfile)
   - `backend/.dockerignore` (replaced by root .dockerignore)
   - `frontend/.dockerignore` (replaced by root .dockerignore)

2. **Environment files:**
   - `backend/.env` (consolidated to root .env)
   - `backend/.env.example` (consolidated to root .env.example)
   - `frontend/.env.example` (no longer needed)

3. **Documentation:**
   - `docs/DOCKER.md` (documented old architecture)
   - `docs/DOCKER_MIGRATION_SUMMARY.md` (obsolete)
   - `docs/DOCKER_QUICK_REFERENCE.md` (obsolete)

## How It Works

### Single Container Architecture

```
User Browser (port 8080)
         ↓
    [nginx:80] ← serves React build
         ↓
    /api/* requests
         ↓
    [uvicorn:8000] ← FastAPI backend
         ↓
    localhost communication (same container)
```

### Process Management

Supervisor runs both services:
- **nginx**: Serves frontend on port 80, proxies API requests
- **uvicorn**: Runs FastAPI backend on port 8000

Both processes run in the same container, communicating via localhost.

### Port Mapping

- **External**: Access via `http://localhost:8080` (or your configured PORT)
- **Container**: nginx listens on port 80 (mapped from PORT)
- **Internal**: uvicorn listens on localhost:8000 (not exposed externally)

## Testing the Migration

### 1. Build and Start

```bash
cd c:\Users\phill\source\KiCAD-Prism

# Build the unified image
docker-compose up -d --build
```

### 2. Check Status

```bash
# View running containers
docker-compose ps

# Should show:
# NAME     SERVICE   STATUS    PORTS
# app      app       running   0.0.0.0:8080->80/tcp
```

### 3. Check Logs

```bash
# View all logs
docker-compose logs -f

# Look for:
# - "Supervisor started with pid X"
# - "nginx entered RUNNING state"  
# - "backend entered RUNNING state"
# - "Application startup complete"
```

### 4. Test Access

```bash
# Frontend (should load React app)
Start-Process "http://localhost:8080"

# Backend health check (should return {"status": "ok"})
curl http://localhost:8080/api/health

# Or in PowerShell:
Invoke-WebRequest -Uri "http://localhost:8080/api/health"
```

### 5. Verify Authentication

Your `.env` already has these configured:
- `ADMIN_EMAIL=admin@resonancegroupusa.com`
- `ADMIN_PASSWORD=[your password]`
- GitHub OAuth credentials
- GitHub App credentials

Try logging in with the admin account to verify authentication works.

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart after .env changes
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# Check container status
docker-compose ps

# Execute command in container
docker-compose exec app bash

# View supervisor process status (inside container)
docker-compose exec app supervisorctl status
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Common issues:
# - Port 8080 already in use: Change PORT in .env
# - Build errors: Check Dockerfile syntax
# - Missing dependencies: Rebuild with --no-cache
docker-compose build --no-cache
```

### Can't access frontend

```bash
# Check nginx is running
docker-compose exec app supervisorctl status nginx

# Check nginx logs
docker-compose exec app tail -f /var/log/nginx/error.log

# Restart nginx
docker-compose exec app supervisorctl restart nginx
```

### API requests failing

```bash
# Check backend is running
docker-compose exec app supervisorctl status backend

# Check backend logs
docker-compose logs | grep backend

# Restart backend
docker-compose exec app supervisorctl restart backend
```

### Environment variables not working

```bash
# Verify variables are passed to container
docker-compose exec app printenv | grep APP_URL

# If missing, check:
# 1. Variable is in .env file
# 2. Variable is listed in docker-compose.yml env_file section
# 3. Restart container: docker-compose restart
```

## Configuration Reference

### Essential Variables (.env)

```env
# Required
PORT=8080
APP_URL=https://kicad.resonancegroupusa.com
ADMIN_EMAIL=admin@resonancegroupusa.com
ADMIN_PASSWORD=your-password
SESSION_SECRET=your-secret
AUTH_ENABLED=true

# OAuth (optional but recommended)
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
GITHUB_ORG_LOGIN=resonance-group
TOKEN_ENCRYPTION_KEY=your-fernet-key

# GitHub App (for repo operations)
GITHUB_APP_ID=your-app-id
GITHUB_APP_PRIVATE_KEY=base64-encoded-key
GITHUB_APP_INSTALLATION_ID=your-installation-id

# SMTP (for email verification)
SMTP_HOST=mail.resonancegroupusa.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password
SMTP_FROM=noreply@resonancegroupusa.com
```

See `.env.example` for complete list.

## Next Steps

1. **Test the build** (see "Testing the Migration" above)
2. **Verify all features work:**
   - Login with admin account
   - Import a project from GitHub
   - View schematics/PCB/3D
   - Add comments
   - Trigger workflows
3. **Check logs for errors** during these operations
4. **Update production deployment** if applicable

## Production Deployment

For production use:

1. Update `.env` with production values:
   ```env
   APP_URL=https://kicad.resonancegroupusa.com
   PORT=80  # or 443 with SSL
   DEV_MODE=false
   ```

2. Consider using Docker secrets for sensitive values:
   - `SESSION_SECRET`
   - `ADMIN_PASSWORD`
   - `GITHUB_APP_PRIVATE_KEY`
   - `SMTP_PASSWORD`

3. Set up SSL/TLS:
   - Use a reverse proxy (nginx, Caddy, Traefik)
   - Or mount certificates and update nginx config

4. Configure backups for:
   - `data/users.db`
   - `data/projects/`
   - `.env` file

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed production guidance.

## Benefits of This Architecture

### Simplicity
- One command to build and run: `docker-compose up -d`
- One configuration file: `.env`
- One image to deploy and manage

### Consistency
- Development workflow identical to production
- No environment-specific configurations
- Same image runs everywhere

### Reduced Complexity
- No container networking configuration
- No service discovery needed
- Simpler debugging (one container to inspect)

### Easier Deployment
- Single image to push/pull from registry
- Fewer moving parts
- Faster startup time

## Questions or Issues?

If you encounter any problems:

1. Check logs: `docker-compose logs -f`
2. Verify `.env` configuration
3. Try rebuilding: `docker-compose up -d --build --no-cache`
4. Check container is running: `docker-compose ps`
5. Inspect supervisor status: `docker-compose exec app supervisorctl status`

The migration preserves all functionality while simplifying the architecture. Everything that worked before should work now, just with a simpler setup.
