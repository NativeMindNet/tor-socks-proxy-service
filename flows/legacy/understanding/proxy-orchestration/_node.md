# Understanding: Proxy Orchestration

> Docker container lifecycle for Tor SOCKS5 proxies

## Phase: EXPLORING

## Hypothesis

This domain handles the containerized Tor runtime - how individual proxy instances are packaged, configured, and managed as Docker containers.

## Sources

- `docker/tor/Dockerfile` - Tor container image definition
- `docker/tor/test.torrc` - Default/test Tor configuration
- `api/main.py:108-123` - torrc generation logic
- `api/main.py:183-255` - Container creation logic
- `docker-compose.yml:4-21` - Base tor-proxy service definition

## Validated Understanding

### Container Image (`docker/tor/Dockerfile`)

Minimal Alpine-based Tor image:

```dockerfile
FROM alpine:latest
RUN apk add --no-cache tor
EXPOSE 9050
RUN mkdir -p /var/lib/tor && chown -R tor:tor /var/lib/tor && chmod 0700 /var/lib/tor
USER tor
CMD ["tor", "-f", "/var/lib/tor/torrc"]
```

**Key Characteristics**:
- Minimal footprint (Alpine base)
- Runs as non-root `tor` user
- Single exposed port (9050)
- Expects torrc at `/var/lib/tor/torrc` by default

### Dynamic torrc Generation

The API generates custom torrc configurations per proxy:

```python
def generate_torrc(socks_port: int, exit_node_ip: str = None, exit_node_fingerprint: str = None):
    torrc_content = f"""
SocksPort 0.0.0.0:{socks_port}
DataDirectory /var/lib/tor
Log notice stdout
ClientOnly 1
StrictNodes 1
"""
    if exit_node_ip:
        torrc_content += f"ExitNodes {exit_node_ip}\n"
    elif exit_node_fingerprint:
        torrc_content += f"ExitNodes {exit_node_fingerprint}\n"

    torrc_content += "ExitRelay 0\n"
    return torrc_content.strip()
```

**Configuration Options**:
- `ClientOnly 1` - Never act as relay
- `StrictNodes 1` - Only use specified exit nodes
- `ExitRelay 0` - Disable exit relay functionality
- `ExitNodes` - Target IP (strict mode) or fingerprint (flexible mode)

### Container Lifecycle

**Creation** (`api/main.py:183-255`):
1. Select random exit node from SQLite
2. Generate torrc with exit node constraint
3. Write torrc to shared volume (`/etc/tor_configs/torrc_{fingerprint}_{timestamp}`)
4. Launch container with:
   - Image: `tor-proxy-image:latest`
   - Ports: `9050/tcp` → dynamic host port
   - Volume: `socks-proxy_tor_configs_data` (read-only)
   - Command: `tor -f /etc/tor_configs/{config_file}`
   - Labels: `com.example.proxy_info` (JSON metadata)
   - Auto-remove on stop

**Termination** (`api/main.py:257-284`):
1. Find container by host port mapping
2. Extract config file path from container command
3. Delete config file from shared volume
4. Stop container (auto-removes)

### Resource Constraints

From `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '0.50'
      memory: 128M
```

### Naming Convention

Container names follow pattern: `tor-proxy-{fingerprint[:12]}-{timestamp}`
- Enables identification of which exit node was selected
- Timestamp prevents naming collisions

## Children

| Child | Status | Rationale |
|-------|--------|-----------|
| [none] | - | Orchestration is leaf domain - Tor internals are external |

## Flow Recommendation

**Type**: SDD (Spec-Driven Development)

**Confidence**: HIGH

**Rationale**:
- Infrastructure component, not user-facing
- Clear technical specification (Docker + Tor)
- No stakeholder communication needs

## Bubble Up

- **Purpose**: Containerized Tor proxy runtime
- **Image**: Alpine-based, minimal, non-root
- **Config**: Dynamic torrc per proxy with geo-specific exit nodes
- **Lifecycle**: API-driven create/destroy with auto-cleanup
- **Isolation**: Each proxy is independent container
- **Constraints**: 0.5 CPU, 128M RAM per instance

---

*Created by /legacy ENTERING phase*
*Updated by /legacy EXPLORING phase*
