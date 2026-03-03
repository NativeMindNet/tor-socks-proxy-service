# ADR-004: Self-hosted CI/CD Runners

## Meta
- **Number**: ADR-004
- **Type**: constraining
- **Status**: APPROVED
- **Created**: 2026-03-03
- **Decided**: 2026-03-03
- **Author**: /legacy analysis
- **Reviewers**: -

## Context

The deployment pipeline needs to build Docker images and deploy containers to target servers. GitHub Actions is the CI/CD platform, but the deployment target is private infrastructure not accessible from the public internet. Options include:

1. GitHub-hosted runners with push to registry, then pull on server
2. Self-hosted runners on each deployment target
3. SSH deployment from GitHub-hosted runners

## Decision Drivers

- Deployment targets are private servers (not publicly accessible)
- Multiple environments needed (prod, dev, stage)
- Docker builds should happen close to deployment
- Minimize complexity of secrets management
- Keep deployment fast (no large image transfers)

## Considered Options

### Option 1: GitHub-hosted Runners + Registry

**Description**: Build images on GitHub-hosted runners, push to container registry, SSH to servers to pull and deploy.

**Pros**:
- No runner maintenance
- Standard approach
- Images versioned in registry

**Cons**:
- Requires container registry (DockerHub, GHCR)
- Image push/pull bandwidth
- SSH keys as GitHub secrets
- Servers need internet access for pulls

### Option 2: Self-hosted Runners per Environment

**Description**: Install GitHub Actions runner on each deployment server, labeled by environment (prod, dev, stage).

**Pros**:
- Direct access to deployment target
- No image registry needed
- Build and deploy on same machine
- No SSH key management
- Works on air-gapped networks

**Cons**:
- Must maintain runner on each server
- Runner security is user responsibility
- Runner updates needed periodically

### Option 3: SSH Deployment from GitHub-hosted

**Description**: Use GitHub-hosted runners with SSH action to connect to servers and run deployment commands.

**Pros**:
- No local runner maintenance
- Central control

**Cons**:
- Servers must be internet-accessible
- SSH keys in GitHub secrets
- Complex secret management for multiple environments
- Can't access Docker daemon directly

## Decision

We will use **Option 2: Self-hosted Runners per Environment** because:

1. Deployment servers are private (not internet-accessible)
2. Build-on-target eliminates image transfer overhead
3. Runner labels (prod/dev/stage) enable branch-based routing
4. DEPLOY_DIR environment variable on runner provides deployment path
5. No secrets needed in GitHub (runner has local access)

## Consequences

### Positive
- Simple branch → environment mapping (push to `prod` → runs on prod runner)
- Fast deployments (no image transfers)
- Runners have direct Docker daemon access
- Works on isolated networks
- Manual dispatch option for flexibility

### Negative
- Must maintain runner service on each server
- Runner security depends on server security
- If runner goes offline, deploys fail
- Runner updates are manual responsibility

### Neutral
- `DEPLOY_DIR` must be set on each runner's environment
- `.env` files managed on servers, not in repo

## Related Decisions
- ADR-001: Containerized Tor Instances (what gets deployed)
- ADR-005: Docker Socket Access (used during deployment)

## Implementation References
- `.github/workflows/deploy.yml` - Complete workflow
- `.github/workflows/deploy.yml:20-25` - Runner selection by label
- `.github/workflows/deploy.yml:44-71` - Environment validation

## Tags
cicd deployment github-actions infrastructure
