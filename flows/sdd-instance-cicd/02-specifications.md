# Specifications: Instance CI/CD

> Version: 1.2
> Status: APPROVED
> Last Updated: 2026-02-12
> Requirements: ./01-requirements.md

## Overview

CI/CD система для автоматического деплоя tor-socks-proxy-service на инстансы prod/dev/stage через GitHub Actions с self-hosted runners.

**Ключевые особенности:**
- Мульти-платформенность: Linux (Ubuntu) + macOS
- Запуск нескольких окружений на одном сервере через изоляцию по IP и тегам
- Platform-specific сервисы через Docker Compose profiles

## Multi-Platform Support

### Platform Matrix

| Platform | Docker | Paths | cadvisor | Network |
|----------|--------|-------|----------|---------|
| Linux/Ubuntu | Docker Engine | `/opt/tor-proxy/` | Yes (profile: linux) | Real IPs |
| macOS | Docker Desktop | `~/tor-proxy/` | No | 127.0.0.1 / host IPs |

### Configuration per Platform

**Linux Runner:**
```bash
# ~/.bashrc or systemd environment
export DEPLOY_DIR=/opt/tor-proxy
```

**macOS Runner:**
```bash
# ~/.zshrc or launchd environment
export DEPLOY_DIR=/Users/username/tor-proxy
```

### Docker Compose Profiles

```yaml
services:
  cadvisor:
    profiles: ["linux"]  # Only starts with --profile linux
    # ...
```

**Запуск:**
```bash
# Linux - с cadvisor
docker-compose --profile linux up -d

# macOS - без cadvisor
docker-compose up -d
```

### Workflow Adaptation

```yaml
- name: Deploy
  run: |
    # DEPLOY_DIR comes from runner environment
    ENV_NAME="${{ github.ref_name }}"
    TARGET_DIR="${DEPLOY_DIR}/${ENV_NAME}"

    # Detect OS for profile
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
      PROFILE_FLAG="--profile linux"
    else
      PROFILE_FLAG=""
    fi

    cd "${TARGET_DIR}"
    docker-compose build
    docker-compose down
    docker-compose ${PROFILE_FLAG} up -d
```

## Affected Systems

| System | Impact | Notes |
|--------|--------|-------|
| `.github/workflows/` | Create | Новый workflow для деплоя |
| `docker-compose.yml` | Modify | Параметризация портов, IP, тегов, логов |
| `.env.example` | Create | Шаблон переменных окружения |
| Dockerfiles | Modify | Добавить вывод логов в файл (если нужно) |

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ branch:prod │  │ branch:dev  │  │ branch:stage│              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │  .github/workflows/   │                          │
│              │     deploy.yml        │                          │
│              └───────────┬───────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │ triggers
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Server: Prod   │ │  Server: Dev    │ │  Server: Stage  │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ GH Runner │  │ │  │ GH Runner │  │ │  │ GH Runner │  │
│  │ label:prod│  │ │  │ label:dev │  │ │  │label:stage│  │
│  └─────┬─────┘  │ │  └─────┬─────┘  │ │  └─────┬─────┘  │
│        ▼        │ │        ▼        │ │        ▼        │
│ /opt/tor-proxy/ │ │ /opt/tor-proxy/ │ │ /opt/tor-proxy/ │
│    └── prod/    │ │    └── dev/     │ │    └── stage/   │
│       ├─ .env   │ │       ├─ .env   │ │       ├─ .env   │
│       ├─ logs/  │ │       ├─ logs/  │ │       ├─ logs/  │
│       └─ ...    │ │       └─ ...    │ │       └─ ...    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Multi-Environment on Single Server

```
┌────────────────────────────────────────────────────────────┐
│                     Single Server                          │
│                                                            │
│  ┌─────────────────────┐    ┌─────────────────────┐       │
│  │   Dev Environment   │    │  Prod Environment   │       │
│  │   IP: 10.0.0.2      │    │   IP: 10.0.0.1      │       │
│  │   Tag: :dev         │    │   Tag: :prod        │       │
│  │                     │    │                     │       │
│  │ ┌─────┐ ┌─────────┐ │    │ ┌─────┐ ┌─────────┐ │       │
│  │ │ tor │ │   api   │ │    │ │ tor │ │   api   │ │       │
│  │ │:9050│ │  :8000  │ │    │ │:9050│ │  :8000  │ │       │
│  │ └─────┘ └─────────┘ │    │ └─────┘ └─────────┘ │       │
│  │                     │    │                     │       │
│  │ /opt/tor-proxy/dev/ │    │ /opt/tor-proxy/prod/│       │
│  └─────────────────────┘    └─────────────────────┘       │
│                                                            │
│  GH Runner (labels: dev, prod)                            │
└────────────────────────────────────────────────────────────┘
```

### Deploy Flow

```
Push to branch (prod/dev/stage)
         │
         ▼
┌─────────────────────────────┐
│ GitHub Actions Triggered    │
│ - Select runner by label    │
│ - runs-on: [self-hosted, X] │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Checkout code               │
│ - Только docker-compose.yml │
│ - И исходники для build     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Copy to deploy dir          │
│ /opt/tor-proxy/{env}/       │
│ - Preserve .env             │
│ - Preserve override.yml     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Build images locally        │
│ docker-compose build        │
│ (uses ENV_TAG from .env)    │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Restart services            │
│ docker-compose down         │
│ docker-compose up -d        │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Health check (optional)     │
│ curl http://$BIND_IP:$PORT  │
└─────────────────────────────┘
```

## Interfaces

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [prod, dev, stage]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options: [prod, dev, stage]

jobs:
  deploy:
    runs-on: [self-hosted, "${{ github.ref_name }}"]
    # При workflow_dispatch: runs-on: [self-hosted, "${{ inputs.environment }}"]

    steps:
      - uses: actions/checkout@v4

      - name: Validate environment
        run: |
          if [ -z "${DEPLOY_DIR}" ]; then
            echo "::error::DEPLOY_DIR not set in runner environment"
            exit 1
          fi
          echo "DEPLOY_DIR=${DEPLOY_DIR}"

      - name: Deploy
        run: |
          ENV_NAME="${{ github.ref_name }}"
          TARGET_DIR="${DEPLOY_DIR}/${ENV_NAME}"

          # Verify .env exists
          if [ ! -f "${TARGET_DIR}/.env" ]; then
            echo "::error::.env not found in ${TARGET_DIR}"
            exit 1
          fi

          # Copy repo files (preserve .env and override.yml)
          cp docker-compose.yml "${TARGET_DIR}/"
          cp -r docker/ "${TARGET_DIR}/"
          cp -r api/ "${TARGET_DIR}/"
          cp -r monitoring/ "${TARGET_DIR}/"
          cp .env.example "${TARGET_DIR}/"

          # Detect OS for profile
          cd "${TARGET_DIR}"
          if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            PROFILE_FLAG="--profile linux"
          else
            PROFILE_FLAG=""
          fi

          # Build and restart
          docker-compose build
          docker-compose down
          docker-compose ${PROFILE_FLAG} up -d

      - name: Health check
        run: |
          sleep 10
          TARGET_DIR="${DEPLOY_DIR}/${{ github.ref_name }}"
          docker-compose -f "${TARGET_DIR}/docker-compose.yml" ps

          # Check containers are running (warning only)
          RUNNING=$(docker-compose -f "${TARGET_DIR}/docker-compose.yml" ps --services --filter "status=running" | wc -l)
          if [ "$RUNNING" -lt 3 ]; then
            echo "::warning::Only ${RUNNING} services running, expected at least 3"
          fi
```

### Parameterized docker-compose.yml

```yaml
version: '3.8'

services:
  tor-proxy:
    build:
      context: ./docker/tor
      dockerfile: Dockerfile
    image: tor-proxy-image:${ENV_TAG:-latest}
    ports:
      - "${BIND_IP:-0.0.0.0}:${TOR_PORT:-9050}:9050"
    volumes:
      - ./docker/tor/torrc:/etc/tor/torrc
      - ${LOGS_DIR:-./logs}/tor:/var/log/tor
    restart: unless-stopped
    networks:
      - tor_network_${ENV_TAG:-default}

  node-discovery:
    build:
      context: .
      dockerfile: docker/node-discovery/Dockerfile
    image: node-discovery-image:${ENV_TAG:-latest}
    volumes:
      - db_data_${ENV_TAG:-default}:/app/db
      - ${LOGS_DIR:-./logs}/node-discovery:/app/logs
    restart: unless-stopped
    networks:
      - tor_network_${ENV_TAG:-default}

  api:
    build:
      context: .
      dockerfile: docker/api/Dockerfile
    image: tor-manager-api-image:${ENV_TAG:-latest}
    ports:
      - "${BIND_IP:-0.0.0.0}:${API_PORT:-8000}:8000"
    volumes:
      - db_data_${ENV_TAG:-default}:/app/db
      - tor_configs_${ENV_TAG:-default}:/etc/tor_configs
      - /var/run/docker.sock:/var/run/docker.sock
      - ${LOGS_DIR:-./logs}/api:/app/logs
    depends_on:
      - node-discovery
    restart: unless-stopped
    networks:
      - tor_network_${ENV_TAG:-default}

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data_${ENV_TAG:-default}:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "${BIND_IP:-0.0.0.0}:${PROMETHEUS_PORT:-9090}:9090"
    restart: unless-stopped
    networks:
      - tor_network_${ENV_TAG:-default}

  grafana:
    image: grafana/grafana:latest
    ports:
      - "${BIND_IP:-0.0.0.0}:${GRAFANA_PORT:-3000}:3000"
    volumes:
      - grafana_data_${ENV_TAG:-default}:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped
    networks:
      - tor_network_${ENV_TAG:-default}

  cadvisor:
    profiles: ["linux"]  # Linux-only, skip on macOS
    image: gcr.io/cadvisor/cadvisor:latest
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    ports:
      - "${BIND_IP:-0.0.0.0}:${CADVISOR_PORT:-8080}:8080"
    restart: unless-stopped
    networks:
      - tor_network_${ENV_TAG:-default}

networks:
  tor_network_${ENV_TAG:-default}:
    driver: bridge
    name: tor_network_${ENV_TAG:-default}

volumes:
  db_data_${ENV_TAG:-default}:
    name: db_data_${ENV_TAG:-default}
  tor_configs_${ENV_TAG:-default}:
    name: tor_configs_${ENV_TAG:-default}
  prometheus_data_${ENV_TAG:-default}:
    name: prometheus_data_${ENV_TAG:-default}
  grafana_data_${ENV_TAG:-default}:
    name: grafana_data_${ENV_TAG:-default}
```

**Note:** Docker Compose не поддерживает переменные в именах networks/volumes напрямую. Решение: использовать `COMPOSE_PROJECT_NAME`.

### Revised Approach: COMPOSE_PROJECT_NAME

```yaml
# docker-compose.yml (simplified)
version: '3.8'

services:
  tor-proxy:
    build:
      context: ./docker/tor
    image: tor-proxy-image:${ENV_TAG:-latest}
    ports:
      - "${BIND_IP:-0.0.0.0}:${TOR_PORT:-9050}:9050"
    volumes:
      - ./docker/tor/torrc:/etc/tor/torrc
      - ${LOGS_DIR:-./logs}/tor:/var/log/tor
    restart: unless-stopped

  # ... other services ...

networks:
  default:
    driver: bridge

volumes:
  db_data:
  tor_configs:
  prometheus_data:
  grafana_data:
```

```bash
# .env
COMPOSE_PROJECT_NAME=tor-proxy-prod
ENV_TAG=prod
BIND_IP=10.0.0.1
LOGS_DIR=/opt/tor-proxy/prod/logs

TOR_PORT=9050
API_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
CADVISOR_PORT=8080

GRAFANA_PASSWORD=secure_password_here
```

С `COMPOSE_PROJECT_NAME` все ресурсы (networks, volumes, containers) автоматически префиксируются, обеспечивая изоляцию.

## Data Models

### Environment Variables (.env.example)

```bash
# ===========================================
# Environment Configuration for tor-socks-proxy
# ===========================================
# Copy this file to .env and configure for your environment

# --- Core Settings ---
# Project name prefix (isolates containers, networks, volumes)
COMPOSE_PROJECT_NAME=tor-proxy-dev

# Environment tag for Docker images
ENV_TAG=dev

# --- Network Binding ---
# IP address to bind services (use specific IP for multi-env on same server)
BIND_IP=0.0.0.0

# --- Ports ---
TOR_PORT=9050
API_PORT=8000
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
CADVISOR_PORT=8080

# --- Paths ---
# Directory for application logs (mounted from host)
LOGS_DIR=./logs

# --- Credentials ---
GRAFANA_PASSWORD=admin

# ===========================================
# Example configurations:
# ===========================================
#
# Linux - Production (IP: 10.0.0.1):
#   COMPOSE_PROJECT_NAME=tor-proxy-prod
#   ENV_TAG=prod
#   BIND_IP=10.0.0.1
#   LOGS_DIR=/opt/tor-proxy/prod/logs
#
# Linux - Development (IP: 10.0.0.2):
#   COMPOSE_PROJECT_NAME=tor-proxy-dev
#   ENV_TAG=dev
#   BIND_IP=10.0.0.2
#   LOGS_DIR=/opt/tor-proxy/dev/logs
#
# macOS - Stage (localhost):
#   COMPOSE_PROJECT_NAME=tor-proxy-stage
#   ENV_TAG=stage
#   BIND_IP=127.0.0.1
#   LOGS_DIR=./logs
```

### Directory Structure on Server

**Linux (`DEPLOY_DIR=/opt/tor-proxy`):**
```
/opt/tor-proxy/
├── prod/
│   ├── .env                         # Production config
│   ├── docker-compose.yml           # From repo (updated on deploy)
│   ├── docker-compose.override.yml  # Local overrides (persistent)
│   ├── docker/                      # Dockerfiles (from repo)
│   ├── api/                         # Source code (from repo)
│   ├── monitoring/                  # Configs (from repo)
│   └── logs/
│       ├── tor/
│       ├── api/
│       └── node-discovery/
├── dev/
│   └── ...
└── stage/
    └── ...
```

**macOS (`DEPLOY_DIR=~/tor-proxy`):**
```
~/tor-proxy/
├── stage/
│   ├── .env                         # BIND_IP=127.0.0.1
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml
│   ├── docker/
│   ├── api/
│   ├── monitoring/
│   └── logs/
└── dev/
    └── ...
```

## Behavior Specifications

### Happy Path: Push to Branch

1. Developer pushes to `dev` branch
2. GitHub Actions triggers `deploy.yml`
3. Job runs on runner with label `dev`
4. Runner checks out code to temp directory
5. Files copied to `/opt/tor-proxy/dev/` (preserving .env, override.yml)
6. `docker-compose build` builds images with tag `:dev`
7. `docker-compose down` stops current containers
8. `docker-compose up -d` starts new containers
9. Health check verifies containers are running
10. Workflow completes successfully

### Happy Path: Manual Deploy

1. User triggers workflow_dispatch
2. Selects environment (e.g., `prod`)
3. Same flow as push, but on selected environment

### Edge Cases

| Case | Trigger | Expected Behavior |
|------|---------|-------------------|
| Missing .env | First deploy or .env deleted | Workflow fails with clear error message |
| Build failure | Dockerfile error or dependency issue | Containers not restarted, old version keeps running |
| Port conflict | Another process using the port | docker-compose up fails, error logged |
| Disk full | No space for images/logs | Build fails, old containers keep running |
| Runner offline | Server down or runner not running | Job queued until runner available |

### Error Handling

| Error | Cause | Response |
|-------|-------|----------|
| `.env not found` | Missing config file | Exit with error, don't touch running containers |
| `docker-compose build` fails | Bad Dockerfile | Exit, keep old containers running |
| `docker-compose up` fails | Port conflict, resource issue | Log error, attempt `docker-compose down` to clean up |
| Health check fails | Service didn't start | Log warning (don't fail workflow) |

## Dependencies

### Requires (Pre-requisites on Server)

- Docker Engine installed
- Docker Compose v2 installed
- GitHub Actions Runner installed and registered
- Runner labeled with environment name (prod/dev/stage)
- `/opt/tor-proxy/{env}/` directory created
- `.env` file configured in deploy directory

### Runner Labels

| Environment | Runner Labels |
|-------------|---------------|
| prod | `self-hosted`, `prod` |
| dev | `self-hosted`, `dev` |
| stage | `self-hosted`, `stage` |

## Testing Strategy

### Manual Verification

1. [ ] Push to `dev` branch → verify containers restart with `:dev` tag
2. [ ] Push to `prod` branch → verify containers restart with `:prod` tag
3. [ ] Run two environments on same server → verify no port conflicts
4. [ ] Check logs appear in `/opt/tor-proxy/{env}/logs/`
5. [ ] Verify `.env` is preserved after deploy
6. [ ] Kill container manually → verify it auto-restarts
7. [ ] Test workflow_dispatch manual trigger

### Verification Commands

```bash
# Check containers are running with correct tags
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"

# Verify network isolation
docker network ls | grep tor

# Check logs directory
ls -la /opt/tor-proxy/prod/logs/

# Verify env is loaded
docker-compose config | grep BIND_IP
```

## Migration / Rollout

### Initial Setup per Server

#### Linux (Ubuntu)

1. Install Docker Engine and Docker Compose
2. Install and register GitHub Runner with label (e.g., `prod`, `dev`)
3. Set `DEPLOY_DIR` in runner environment:
   ```bash
   # Add to ~/.bashrc or /etc/environment
   export DEPLOY_DIR=/opt/tor-proxy
   ```
4. Create directory structure:
   ```bash
   sudo mkdir -p /opt/tor-proxy/{prod,dev,stage}/{logs/tor,logs/api,logs/node-discovery}
   sudo chown -R $USER:$USER /opt/tor-proxy/
   ```
5. Copy `.env.example` to `.env` in each environment dir and configure
6. First deploy will copy all files and build images

#### macOS

1. Install Docker Desktop
2. Install and register GitHub Runner with label (e.g., `stage`)
3. Set `DEPLOY_DIR` in runner environment:
   ```bash
   # Add to ~/.zshrc
   export DEPLOY_DIR=~/tor-proxy
   ```
4. Create directory structure:
   ```bash
   mkdir -p ~/tor-proxy/{stage,dev}/{logs/tor,logs/api,logs/node-discovery}
   ```
5. Copy `.env.example` to `.env` and configure (use `BIND_IP=127.0.0.1`)
6. First deploy will copy all files and build images

**Note:** cadvisor не запускается на macOS (Linux-only). Workflow автоматически определит OS и пропустит его.

### Existing Server Migration

1. Stop current containers: `docker-compose down`
2. Move existing files to `/opt/tor-proxy/{env}/`
3. Create `.env` from `.env.example`
4. Configure `BIND_IP`, `ENV_TAG`, etc.
5. Test: `docker-compose up -d`

## Open Design Questions

- [x] Как изолировать networks/volumes? → Через `COMPOSE_PROJECT_NAME`
- [x] Нужен ли отдельный workflow файл для каждого окружения или один универсальный? → **Один универсальный `deploy.yml`**
- [x] Стратегия при падении health check — fail workflow или warning? → **Warning only** (не fail)
- [x] Как поддержать macOS + Linux? → **DEPLOY_DIR в env runner'а, profiles для linux-only сервисов**
- [x] Как обрабатывать cadvisor на macOS? → **Docker Compose profiles: `["linux"]`**

---

## Approval

- [x] Reviewed by: User
- [x] Approved on: 2026-02-12
- [x] Notes: Multi-platform support (Linux + macOS) added
