# ADR-005: Docker Socket Access

## Meta
- **Number**: ADR-005
- **Type**: enabling
- **Status**: APPROVED
- **Created**: 2026-03-03
- **Decided**: 2026-03-03
- **Author**: /legacy analysis
- **Reviewers**: -

## Context

The FastAPI service needs to dynamically create and destroy Tor proxy containers. This requires programmatic access to the Docker daemon. The service runs inside a container itself, so it needs a mechanism to control the host's Docker daemon.

Options for container-to-container management:
1. Mount the Docker socket into the API container
2. Use Docker-in-Docker (DinD)
3. External orchestrator (e.g., separate daemon)

## Decision Drivers

- API must create/destroy containers on demand
- Simple implementation preferred
- Must work within Docker Compose environment
- Need to list, inspect, and manage container lifecycle
- Low latency container operations

## Considered Options

### Option 1: Docker Socket Mount

**Description**: Mount `/var/run/docker.sock` from the host into the API container, use Docker SDK.

**Pros**:
- Direct, fast access to Docker daemon
- Full Docker API available
- Docker SDK (docker-py) is mature
- Simple configuration (volume mount)
- Containers created are host-level (not nested)

**Cons**:
- Security concern: container has root-equivalent access
- Breaking out of container possible if compromised
- Socket path is Linux-specific

### Option 2: Docker-in-Docker (DinD)

**Description**: Run a Docker daemon inside the API container.

**Pros**:
- Isolated from host Docker
- No socket mount needed

**Cons**:
- Complex setup
- Performance overhead
- Nested containers (harder to manage)
- Storage driver complications
- Not recommended by Docker

### Option 3: External Orchestrator

**Description**: Separate service manages containers, API calls it via HTTP.

**Pros**:
- Better separation of concerns
- Could add authorization layer
- API doesn't need Docker access

**Cons**:
- Additional service to build and maintain
- More complex architecture
- Higher latency for operations
- Overkill for this use case

## Decision

We will use **Option 1: Docker Socket Mount** because:

1. Simplest path to Docker daemon access
2. Docker SDK provides clean Python API
3. Created containers are first-class host containers
4. No additional services or complexity
5. Well-documented pattern for container management tools

## Consequences

### Positive
- Full Docker API access via Python SDK
- Fast container operations (direct socket)
- Containers appear on host (easy to inspect/debug)
- Standard pattern used by many tools (Portainer, etc.)
- Simple single-line volume mount in compose

### Negative
- **Security risk**: Compromised API container = host compromise
- Container runs with elevated privileges effectively
- Must trust all code running in API container
- Linux-specific (macOS has different socket path)

### Neutral
- Recommend running API on isolated network
- Consider API authentication if exposed externally
- Regular security audits advised

## Mitigations

1. **Network isolation**: API only accessible from internal network
2. **No external exposure**: BIND_IP can restrict to localhost
3. **Container resource limits**: Prevent resource exhaustion
4. **Read-only where possible**: API code mounted read-only

## Related Decisions
- ADR-001: Containerized Tor Instances (what gets managed)

## Implementation References
- `docker-compose.yml:50` - Socket mount configuration
- `api/main.py:80-86` - Docker client initialization
- `api/main.py:212-227` - Container creation via SDK

## Tags
security docker architecture infrastructure
