# Understanding: Deployment

> Docker Compose and CI/CD pipeline

## Phase: EXPLORING

## Hypothesis

Infrastructure-as-code for local development and multi-environment CI/CD deployment using Docker Compose and GitHub Actions with self-hosted runners.

## Sources

- `docker-compose.yml` - Service orchestration (115 lines)
- `.env.example` - Environment configuration template
- `.github/workflows/deploy.yml` - CI/CD workflow (156 lines)
- `update.sh` - Manual git sync script

## Validated Understanding

### Docker Compose Architecture

Six services orchestrated in `tor_manager_network`:

```
┌─────────────────────────────────────────────────────────────────┐
│                    docker-compose.yml                           │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────┤
│ tor-proxy   │ api         │ node-disc.  │ prometheus  │ grafana │
│ (Tor image) │ (FastAPI)   │ (Python)    │ (metrics)   │ (viz)   │
├─────────────┴─────────────┴─────────────┴─────────────┴─────────┤
│                     + cadvisor (Linux only)                     │
└─────────────────────────────────────────────────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
    ┌───────────┐     ┌───────────┐     ┌───────────┐
    │ db_data   │     │ tor_cfg   │     │ prom_data │
    │ (SQLite)  │     │ (torrc)   │     │ (metrics) │
    └───────────┘     └───────────┘     └───────────┘
```

### Environment Configuration (`.env.example`)

| Variable | Purpose | Default |
|----------|---------|---------|
| `COMPOSE_PROJECT_NAME` | Container namespace | `tor-proxy-dev` |
| `ENV_TAG` | Image tag | `dev` |
| `BIND_IP` | Network binding | `0.0.0.0` |
| `TOR_PORT` | Tor SOCKS port | `9050` |
| `API_PORT` | FastAPI port | `8000` |
| `PROMETHEUS_PORT` | Prometheus port | `9090` |
| `GRAFANA_PORT` | Grafana port | `3000` |
| `CADVISOR_PORT` | cAdvisor port | `8080` |
| `GRAFANA_PASSWORD` | Admin password | `admin` |

**Multi-Environment Strategy**:
- Different `COMPOSE_PROJECT_NAME` for isolation
- Different `BIND_IP` for same-server deployments
- Different `ENV_TAG` for image versioning

### CI/CD Pipeline (`.github/workflows/deploy.yml`)

**Trigger Conditions**:
- Push to `prod`, `dev`, or `stage` branches
- Manual dispatch with environment selection

**Runner Selection**:
```yaml
runs-on:
  - self-hosted
  - ${{ github.event_name == 'workflow_dispatch' && inputs.environment || github.ref_name }}
```
Uses branch name as runner label (e.g., push to `prod` → runs on `self-hosted, prod` runner).

**Deployment Steps**:

1. **Checkout** - Get latest code

2. **Validate Environment** - Check:
   - `DEPLOY_DIR` env var is set on runner
   - `${DEPLOY_DIR}/${env_name}` directory exists
   - `.env` file present in target directory

3. **Deploy** - Execute:
   ```bash
   # Copy files (preserves .env)
   cp docker-compose.yml "${TARGET_DIR}/"
   cp -r docker/ api/ monitoring/ "${TARGET_DIR}/"

   # OS detection for profile
   if [[ "$OSTYPE" == "linux-gnu"* ]]; then
       PROFILE_FLAG="--profile linux"  # Include cadvisor
   fi

   # Build and restart
   docker-compose build
   docker-compose down --remove-orphans
   docker-compose ${PROFILE_FLAG} up -d
   ```

4. **Health Check** - Verify:
   - Wait 10 seconds
   - Check container count (expect 5 minimum)
   - Show recent logs

**Key Design Decisions**:
- Self-hosted runners (not GitHub-hosted)
- Runner per environment (labeled)
- `.env` preserved on target, not overwritten
- cAdvisor conditional on OS type

### Volume Persistence

| Volume | Purpose | Mounted By |
|--------|---------|------------|
| `db_data` | SQLite database | node-discovery, api |
| `tor_configs_data` | Dynamic torrc files | api |
| `prometheus_data` | Metrics storage | prometheus |
| `grafana_data` | Dashboards/config | grafana |

### Network

Single bridge network (`tor_manager_network`) enables:
- Service discovery by name (e.g., `api:8000`)
- Internal communication isolation

## Children

| Child | Status | Rationale |
|-------|--------|-----------|
| [none] | - | Standard Docker/CI patterns, no custom sub-systems |

## Flow Recommendation

**Type**: SDD (Spec-Driven Development)

**Confidence**: HIGH

**Rationale**:
- Infrastructure automation
- Clear technical specifications
- No stakeholder documentation needs

## Bubble Up

- **Local Dev**: `docker-compose up -d` with `.env` configuration
- **CI/CD**: GitHub Actions with self-hosted runners per environment
- **Multi-Env**: Same server via different IPs/namespaces
- **Volumes**: Persistent data, configs, metrics across restarts
- **OS Handling**: cAdvisor only on Linux

---

*Created by /legacy ENTERING phase*
*Updated by /legacy EXPLORING phase*
