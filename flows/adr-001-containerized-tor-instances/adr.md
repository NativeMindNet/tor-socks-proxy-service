# ADR-001: Containerized Tor Instances

## Meta
- **Number**: ADR-001
- **Type**: enabling
- **Status**: APPROVED
- **Created**: 2026-03-03
- **Decided**: 2026-03-03
- **Author**: /legacy analysis
- **Reviewers**: -

## Context

The legacy socks-proxy system ran Tor instances directly on the host operating system, managed by PHP and shell scripts. This approach had several problems:

1. **Path dependencies**: Scripts hardcoded paths like `/etc/tor/` and `/var/lib/tor/`
2. **No isolation**: All Tor processes shared the host filesystem
3. **Deployment complexity**: Required installing Tor on each target system
4. **Resource management**: No limits on individual proxy instances
5. **Cleanup challenges**: Orphaned processes and data directories accumulated

The modernized system needed a way to run multiple independent Tor proxies with dynamic configuration, proper isolation, and clean lifecycle management.

## Decision Drivers

- Need to run multiple independent Tor proxies simultaneously
- Each proxy requires unique configuration (exit nodes, ports)
- Must support dynamic creation/destruction via API
- Require resource isolation and limits
- Need portable deployment across different environments

## Considered Options

### Option 1: Native Tor Processes

**Description**: Continue running Tor directly on the host, managed by the FastAPI service using subprocess.

**Pros**:
- Lower overhead (no container runtime)
- Simpler debugging (direct process access)
- No Docker dependency

**Cons**:
- No isolation between instances
- Complex cleanup on failure
- Host filesystem pollution
- Difficult to set resource limits
- Platform-specific installation

### Option 2: Containerized Tor Instances (Docker)

**Description**: Each Tor proxy runs in its own Docker container with a dynamically generated torrc configuration.

**Pros**:
- Complete isolation between instances
- Resource limits via Docker cgroups
- Clean lifecycle (container = process lifecycle)
- Portable across any Docker-capable host
- Auto-cleanup on container stop

**Cons**:
- Requires Docker runtime
- Slightly higher resource overhead
- Additional complexity in container management

### Option 3: Kubernetes Pods

**Description**: Deploy Tor proxies as Kubernetes pods with dynamic scaling.

**Pros**:
- Enterprise-grade orchestration
- Built-in scaling and health checks
- Service mesh integration possible

**Cons**:
- Massive overkill for this use case
- Requires Kubernetes cluster
- Significantly more complex deployment
- Higher latency for proxy creation

## Decision

We will use **Option 2: Containerized Tor Instances** because:

1. Docker provides the right level of isolation without Kubernetes complexity
2. The Docker SDK integrates cleanly with FastAPI for container lifecycle management
3. Resource limits protect the host from runaway proxy instances
4. Container auto-removal on stop eliminates cleanup concerns
5. Alpine-based images minimize overhead (~50MB per container)

## Consequences

### Positive
- Each proxy is fully isolated with its own filesystem
- Clean creation/destruction via Docker SDK
- Resource limits prevent single proxy from affecting others
- Portable deployment (any Docker host works)
- torrc configurations stay isolated in container-specific paths

### Negative
- Docker must be installed on the host
- Slight memory overhead per container (~5-10MB)
- API service needs Docker socket access (see ADR-005)
- Container startup adds ~2 seconds to proxy creation time

### Neutral
- Team must understand Docker debugging tools
- Logs accessible via `docker logs` instead of system journald

## Related Decisions
- ADR-005: Docker Socket Access - required for API to manage containers

## Implementation References
- `docker/tor/Dockerfile` - Alpine-based Tor image
- `api/main.py:183-255` - Container creation logic
- `docker-compose.yml:4-21` - Base tor-proxy service

## Tags
architecture docker tor containerization isolation
