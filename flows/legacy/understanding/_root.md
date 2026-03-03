# Understanding: Project Root

> Entry point for recursive understanding. Children are top-level logical domains.

## Phase: COMPLETE

## Project Overview

**Tor SOCKS Proxy Service** - A containerized, API-driven system for dynamically managing Tor SOCKS5 proxies with geo-specific exit nodes. This service replaces a legacy PHP/shell-based system with a modern Python/Docker stack.

### Purpose
Provides on-demand SOCKS5 proxies via Tor network with:
- Geographic exit node selection (US vs NON_US)
- Dynamic proxy lifecycle management via REST API
- Automatic Tor exit node discovery and refresh
- Full observability stack (Prometheus/Grafana)

### Tech Stack
- **API**: FastAPI (Python 3.9) with Prometheus instrumentation
- **Proxy Runtime**: Tor on Alpine Linux containers
- **Node Discovery**: Python script fetching from Onionoo API
- **Data Store**: SQLite (tor_nodes.db, queue.db)
- **Orchestration**: Docker Compose
- **Monitoring**: Prometheus + Grafana + cAdvisor
- **CI/CD**: GitHub Actions (self-hosted runners, multi-env)

## Identified Domains

> Logical domains discovered. Each becomes a child directory for deeper exploration.

| Domain | Hypothesis | Priority | Status |
|--------|------------|----------|--------|
| api-gateway | FastAPI REST interface for proxy management | HIGH | COMPLETE |
| proxy-orchestration | Docker container lifecycle for Tor proxies | HIGH | COMPLETE |
| node-discovery | Tor exit node fetching and database population | MEDIUM | COMPLETE |
| monitoring | Prometheus/Grafana observability stack | MEDIUM | COMPLETE |
| deployment | Docker Compose and CI/CD pipeline | LOW | COMPLETE |

## Source Mapping

> Which source paths map to which logical domains

| Source Path | → Domain |
|-------------|----------|
| api/main.py | api-gateway |
| api/requirements.txt | api-gateway |
| docker/tor/* | proxy-orchestration |
| docker/api/* | api-gateway |
| node_discovery.py | node-discovery |
| docker/node-discovery/* | node-discovery |
| monitoring/* | monitoring |
| docker-compose.yml | deployment, proxy-orchestration |
| .github/workflows/* | deployment |

## Cross-Cutting Concerns

> Things that span multiple domains (may become ADRs)

- **Docker Socket Mounting**: API has direct access to Docker daemon via socket mount - enables dynamic container creation but poses security considerations
- **Shared Volume Strategy**: db_data volume shared between node-discovery and api services for SQLite access
- **Geo-categorization Logic**: US vs NON_US classification embedded in multiple components
- **Container Labeling**: com.example.proxy_info label used for proxy metadata propagation

## Architectural Decisions Detected

1. **ADR: Containerized Tor Instances** - Each proxy runs as isolated Docker container with custom torrc
2. **ADR: Onionoo API for Node Discovery** - Replaced static CSV with official Tor Project API
3. **ADR: SQLite for Node Storage** - Simple file-based database, refreshed entirely on each discovery run
4. **ADR: Self-hosted GitHub Actions Runners** - Multi-environment deployment (prod/dev/stage) via runner labels

## Children Spawned

```
api-gateway         → COMPLETE
proxy-orchestration → COMPLETE
node-discovery      → COMPLETE
monitoring          → COMPLETE
deployment          → COMPLETE
```

## Synthesis

All five logical domains have been analyzed. The project is a well-structured, containerized proxy management system with clear separation of concerns:

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Tor SOCKS Proxy Service                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐  │
│  │ node-disc.  │────►│  SQLite DB  │◄────│      FastAPI (API)      │  │
│  │ (Onionoo)   │     │ tor_nodes   │     │   /proxies, /health     │  │
│  └─────────────┘     └─────────────┘     └───────────┬─────────────┘  │
│       30min                                          │                 │
│                                                      │ Docker SDK      │
│                                                      ▼                 │
│  ┌───────────────────────────────────────────────────────────────┐    │
│  │                    Tor Proxy Containers                        │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │    │
│  │  │ tor-US  │  │ tor-US  │  │tor-NON  │  │tor-NON  │  ...      │    │
│  │  │ :32768  │  │ :32769  │  │ :32770  │  │ :32771  │           │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │    │
│  └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐              │
│  │ Prometheus  │────►│   Grafana   │     │  cAdvisor   │              │
│  │  :9090      │     │    :3000    │     │   :8080     │              │
│  └─────────────┘     └─────────────┘     └─────────────┘              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Findings

1. **Mature Implementation**: All 7 phases in the SDD plan are complete
2. **Clean Architecture**: Each domain has clear boundaries and responsibilities
3. **No Child Domains**: All domains are leaf nodes - no further recursion needed
4. **Existing Documentation**: `flows/sdd-tor-socks-proxy-service/` contains complete SDD artifacts
5. **Flow Recommendation**: SDD is appropriate for all domains (internal infrastructure)

### Gaps/Improvements Identified

1. **No Authentication**: API endpoints are unauthenticated
2. **SQLite Concurrency**: Full refresh strategy avoids concurrent write issues but is not scalable
3. **Dashboard Provisioning**: Grafana dashboards not auto-provisioned (manual setup)
4. **cAdvisor Linux-only**: Container metrics unavailable on macOS

---

*Created by /legacy ENTERING phase*
*Updated by /legacy SYNTHESIZING phase*
*Completed: 2026-03-03*
