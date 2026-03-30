# KiCAD Prism - Quick Start Guide

## One Command Setup

KiCAD Prism uses a single Docker image containing both frontend and backend. Development and production workflows are identical.

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- 4GB+ RAM recommended
- 10GB+ disk space

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd KiCAD-Prism
   ```

2. **Configure environment**:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your settings
   # Minimum required: PORT, APP_URL, ADMIN_EMAIL, ADMIN_PASSWORD, SESSION_SECRET
   ```

3. **Start the application**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Open your browser to `http://localhost:8080` (or your configured PORT)
   - Login with your ADMIN_EMAIL and ADMIN_PASSWORD

### Common Commands

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Restart after config changes
docker-compose restart

# Stop the application
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Check status
docker-compose ps
```

### What's Inside

The single Docker image contains:
- **Frontend**: React + Vite (built and served by nginx)
- **Backend**: FastAPI + Python (running on uvicorn)
- **KiCAD libraries**: Pre-installed KiCAD 9 with Python bindings
- **Supervisor**: Manages both nginx and uvicorn processes

Both services run in the same container and communicate via localhost.

### Environment Configuration

All configuration is in the root `.env` file:

```env
# Port (required)
PORT=8080

# Application URL (required)
APP_URL=http://localhost:8080

# Admin account (required)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password

# Session secret (required)
SESSION_SECRET=your-random-secret-key

# GitHub OAuth (optional but recommended)
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_ORG_LOGIN=your-org
TOKEN_ENCRYPTION_KEY=...

# GitHub App for repo operations (optional)
GITHUB_APP_ID=...
GITHUB_APP_PRIVATE_KEY=...
GITHUB_APP_INSTALLATION_ID=...
GITHUB_WEBHOOK_SECRET=...
```

See `.env.example` for all available options.

### Data Persistence

The following directories are automatically persisted:
- `./data/projects` - Your KiCAD projects
- `./data/ssh` - SSH keys for Git operations
- `./data/users.db` - User database

These are mounted as Docker volumes and persist even when the container is recreated.

### Development Workflow

**There is no separate "development mode"**. The same Docker setup is used for both development and production.

To make code changes:

1. Edit your code
2. Rebuild and restart:
   ```bash
   docker-compose up -d --build
   ```

For faster frontend iteration, you can optionally run the Vite dev server locally (requires Node.js):
```bash
cd frontend
npm install
npm run dev
```

But the Docker approach is simpler and matches production exactly.

### Troubleshooting

**Container won't start**:
```bash
# Check logs
docker-compose logs -f

# Check for port conflicts
netstat -ano | findstr :8080  # Windows
lsof -i :8080                 # macOS/Linux
```

**Can't login**:
- Verify `SESSION_SECRET` is set in `.env`
- Check `AUTH_ENABLED=true` in `.env`
- Check logs: `docker-compose logs -f`

**Port already in use**:
- Edit `PORT=8080` in `.env` to a different port
- Restart: `docker-compose down && docker-compose up -d`

**Need to reset everything**:
```bash
# Stop and remove container
docker-compose down

# Remove all data (⚠️ this deletes projects and users!)
rm -rf data/

# Restart fresh
docker-compose up -d
```

### Production Deployment

For production:

1. Set `APP_URL` to your public domain
2. Use HTTPS and set `SESSION_COOKIE_SECURE=true`
3. Generate strong secrets for `SESSION_SECRET`, `ADMIN_PASSWORD`, etc.
4. Configure GitHub OAuth and GitHub App
5. Set up SMTP for email verification
6. Use a reverse proxy (nginx/Traefik) with SSL certificates
7. Set up automated backups of `./data/` directory

### Next Steps

- Configure GitHub integration for repository access
- Set up SMTP for email verification
- Invite team members and assign roles
- Import your first KiCAD project

For detailed documentation, see:
- [README.md](../README.md) - Full feature documentation
- [.env.example](../.env.example) - All configuration options
- [Architecture](../README.md#architecture) - How it works

## Support

If you encounter issues:
1. Check `docker-compose logs -f`
2. Verify your `.env` configuration
3. Ensure ports are not in use
4. Check Docker Desktop is running
