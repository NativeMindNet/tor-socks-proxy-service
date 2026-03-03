# Code to Flow Mapping

## Overview

Maps analyzed code modules to generated flows.

## Flow Type Detection Rules

| Indicator | Flow Type |
|-----------|-----------|
| `*.test.*`, `*.spec.*`, `__tests__/` | TDD |
| `components/`, `*.tsx`, `*.vue`, `templates/` | VDD |
| `README.md`, public exports, API docs | DDD |
| Internal logic, no UI, no public API | SDD |

## Existing Flows

The project already has a complete SDD flow that covers all domains:

| Flow | Path | Status |
|------|------|--------|
| SDD: tor-socks-proxy-service | `flows/sdd-tor-socks-proxy-service/` | COMPLETE |

## Mapping Table

| Code Path | Flow | Type | Action | Status | Notes |
|-----------|------|------|--------|--------|-------|
| api/main.py | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | FastAPI control plane |
| api/requirements.txt | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Python dependencies |
| node_discovery.py | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Onionoo integration |
| docker/tor/Dockerfile | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Tor container image |
| docker/tor/test.torrc | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Test configuration |
| docker/api/Dockerfile | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | API container image |
| docker/node-discovery/Dockerfile | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Discovery container |
| docker-compose.yml | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Service orchestration |
| .env.example | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Environment config |
| .github/workflows/deploy.yml | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | CI/CD pipeline |
| monitoring/prometheus.yml | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Metrics collection |
| monitoring/grafana/provisioning/* | sdd-tor-socks-proxy-service | SDD | UNCHANGED | COMPLETE | Visualization setup |

### Action Values
- **CREATED** - New flow created
- **UPDATED** - Existing flow appended to (additive changes only)
- **UNCHANGED** - Flow exists, no new information found
- **CONFLICT** - Analysis contradicts existing documentation (needs reconciliation)

## ADR Mapping

| Code Pattern | ADR | Type | Status |
|--------------|-----|------|--------|
| Docker container per proxy | ADR-001: Containerized Tor Instances | enabling | RECOMMENDED |
| Onionoo API calls | ADR-002: Onionoo for Node Discovery | enabling | RECOMMENDED |
| SQLite full refresh | ADR-003: SQLite Node Storage | constraining | RECOMMENDED |
| Self-hosted runners | ADR-004: Self-hosted CI/CD | constraining | RECOMMENDED |
| Docker socket mount | ADR-005: Docker Socket Access | enabling | RECOMMENDED |

## Unmapped (needs manual review)

| Code Path | Reason |
|-----------|--------|
| db/tor_nodes.db | Generated artifact, not source |
| db/queue.db | Generated artifact, not source |
| update.sh | Utility script, minimal complexity |

## Coverage Summary

```
Source Files Analyzed:      12
Files Mapped to Flows:      12
Coverage:                   100%

Flows Referenced:           1 (existing SDD)
New Flows Created:          0
ADRs Recommended:           5
```

---

*Updated by /legacy analysis*
*Date: 2026-03-03*
