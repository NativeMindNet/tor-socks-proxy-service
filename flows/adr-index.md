# ADR Index

Master index of all Architecture Decision Records.

## Active ADRs

| # | Name | Title | Type | Status | Created | Decided | File |
|---|------|-------|------|--------|---------|---------|------|
| 1 | containerized-tor-instances | Containerized Tor Instances | enabling | approved | 2026-03-03 | 2026-03-03 | adr-001-containerized-tor-instances/adr.md |
| 2 | onionoo-node-discovery | Onionoo API for Node Discovery | enabling | approved | 2026-03-03 | 2026-03-03 | adr-002-onionoo-node-discovery/adr.md |
| 3 | sqlite-node-storage | SQLite for Node Storage | constraining | approved | 2026-03-03 | 2026-03-03 | adr-003-sqlite-node-storage/adr.md |
| 4 | self-hosted-cicd-runners | Self-hosted CI/CD Runners | constraining | approved | 2026-03-03 | 2026-03-03 | adr-004-self-hosted-cicd-runners/adr.md |
| 5 | docker-socket-access | Docker Socket Access | enabling | approved | 2026-03-03 | 2026-03-03 | adr-005-docker-socket-access/adr.md |

### Types
- **constraining** - selects from options, closes alternatives
- **enabling** - adds new capabilities, expands scope

## Statistics

- **Total**: 5
- **Approved**: 5
- **Review**: 0
- **Draft**: 0
- **Rejected**: 0
- **Superseded**: 0

## Categories

### Architecture
- ADR-001: Containerized Tor Instances
- ADR-005: Docker Socket Access

### Data
- ADR-002: Onionoo API for Node Discovery
- ADR-003: SQLite for Node Storage

### Infrastructure
- ADR-004: Self-hosted CI/CD Runners

### Security
- ADR-005: Docker Socket Access (security implications noted)

## Relationships

### Dependencies
- ADR-001 depends on ADR-005 (containers need socket access to be managed)
- ADR-003 depends on ADR-002 (SQLite stores data from Onionoo)

### Data Flow
```
ADR-002 (Onionoo) → ADR-003 (SQLite) → ADR-001 (Containers)
                                              ↑
                                        ADR-005 (Socket)
                                              ↑
                                        ADR-004 (CI/CD)
```

### Supersedes
(none)

---

## Index Maintenance

When creating/updating ADRs:
1. Add entry to table above
2. Update statistics
3. Add to relevant category
4. Note any relationships

**Last updated**: 2026-03-03
**Next ADR number**: 6
