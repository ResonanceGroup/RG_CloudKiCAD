# ============================================================================
# KiCAD Prism - Unified Docker Image
# ============================================================================
# This single image contains both the frontend (nginx) and backend (FastAPI).
# Both services run in the same container managed by supervisor.

# Multi-architecture support
ARG TARGETARCH

# Select KiCAD base image based on target architecture
FROM kicad/kicad:9.0.7-amd64 AS base-amd64
FROM kicad/kicad:9.0.0-arm64 AS base-arm64

# ============================================================================
# Stage 1: Build Frontend
# ============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /build/frontend

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci --include=dev

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# ============================================================================
# Stage 2: Final Image with Backend + Frontend
# ============================================================================
FROM base-${TARGETARCH}

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

USER root
WORKDIR /app

# Install required packages:
# - Python, pip, venv for backend
# - git for repository operations
# - nginx for serving frontend
# - supervisor to manage both services
# - wget and curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    git \
    nginx \
    supervisor \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Setup Backend
# ============================================================================
WORKDIR /app/backend

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy backend application code
COPY backend/ ./

# ============================================================================
# Setup Frontend
# ============================================================================
# Copy built frontend from builder stage
COPY --from=frontend-builder /build/frontend/dist /usr/share/nginx/html

# Copy nginx configuration for unified container (backend on localhost:8000)
COPY docker/nginx.conf /etc/nginx/sites-available/default

# Create nginx log directory
RUN mkdir -p /var/log/nginx

# ============================================================================
# Setup Supervisor
# ============================================================================
# Copy supervisor configuration
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# ============================================================================
# Setup Directories and Permissions
# ============================================================================
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p \
    /app/projects \
    /root/.ssh \
    /var/run/supervisor \
    /var/log/supervisor \
    && chmod 700 /root/.ssh

# ============================================================================
# Expose Ports
# ============================================================================
# Port 80 for nginx (frontend + API proxy)
EXPOSE 80

# ============================================================================
# Health Check
# ============================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:80/ && curl -f http://localhost:8000/api/health || exit 1

# ============================================================================
# Startup
# ============================================================================
# Start supervisor which manages both nginx and uvicorn
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
