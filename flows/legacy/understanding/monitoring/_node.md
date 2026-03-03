# Understanding: Monitoring

> Prometheus/Grafana observability stack

## Phase: EXPLORING

## Hypothesis

Standard observability stack providing metrics collection, storage, and visualization for the Tor proxy service.

## Sources

- `monitoring/prometheus.yml` - Prometheus scrape configuration
- `monitoring/grafana/provisioning/datasources/datasource.yml` - Grafana datasource config
- `docker-compose.yml:62-104` - Prometheus, Grafana, cAdvisor services
- `api/main.py:26-78` - Custom Prometheus metrics

## Validated Understanding

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                         │
├─────────────────┬───────────────────┬───────────────────────┤
│   Prometheus    │     Grafana       │     cAdvisor          │
│   (Collector)   │  (Visualization)  │  (Container Metrics)  │
│     :9090       │      :3000        │       :8080           │
└────────┬────────┴─────────┬─────────┴───────────┬───────────┘
         │                  │                     │
         │  scrapes         │  queries            │  scrapes
         ▼                  ▼                     │
    ┌────────────┐    ┌────────────┐              │
    │  FastAPI   │    │ Prometheus │◄─────────────┘
    │  /metrics  │    │            │
    └────────────┘    └────────────┘
```

### Prometheus Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'tor-proxy-api'
    static_configs:
      - targets: ['api:8000']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
```

**Scrape Targets**:
1. Self-monitoring (Prometheus)
2. FastAPI application metrics
3. Container resource metrics (cAdvisor)

### Custom Application Metrics

Defined in `api/main.py`:

```python
# Gauges
active_proxies_gauge = Gauge(
    "tor_proxy_manager_active_proxies",
    "Number of active Tor proxy containers",
    ["geo_category"]  # Labels: US, NON_US
)

available_nodes_gauge = Gauge(
    "tor_proxy_manager_available_exit_nodes",
    "Number of available Tor exit nodes in database",
    ["geo_category"]  # Labels: US, NON_US
)
```

**Metric Update Triggers**:
- Startup
- Health check (`GET /health`)
- Proxy creation/deletion

**Standard HTTP Metrics** (via `prometheus-fastapi-instrumentator`):
- `http_requests_total`
- `http_request_duration_seconds`
- `http_request_size_bytes`
- `http_response_size_bytes`

### Grafana Setup

**Datasource** (auto-provisioned):
```yaml
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

**Container Configuration**:
- Admin password via `GF_SECURITY_ADMIN_PASSWORD` (default: `admin`)
- Sign-up disabled
- Persistent storage: `grafana_data` volume

### cAdvisor

- Provides container-level resource metrics
- Linux-only (profile conditional)
- Monitors CPU, memory, network, filesystem per container

```yaml
profiles: ["linux"]  # Only starts on Linux hosts
```

### Service Ports

| Service | Internal | External (configurable) |
|---------|----------|-------------------------|
| Prometheus | 9090 | `${PROMETHEUS_PORT:-9090}` |
| Grafana | 3000 | `${GRAFANA_PORT:-3000}` |
| cAdvisor | 8080 | `${CADVISOR_PORT:-8080}` |

## Children

| Child | Status | Rationale |
|-------|--------|-----------|
| [none] | - | Standard tooling, no custom sub-components |

## Flow Recommendation

**Type**: SDD (Spec-Driven Development)

**Confidence**: MEDIUM

**Rationale**:
- Infrastructure component
- Mostly off-the-shelf tools
- May need DDD if dashboards become stakeholder-facing

## Bubble Up

- **Purpose**: Observability for proxy service health and performance
- **Components**: Prometheus (collection), Grafana (visualization), cAdvisor (containers)
- **Custom Metrics**: Active proxies count, available nodes count by geo
- **Standard Metrics**: HTTP request metrics via FastAPI instrumentator
- **Note**: cAdvisor Linux-only, dashboard provisioning not yet implemented

---

*Created by /legacy ENTERING phase*
*Updated by /legacy EXPLORING phase*
