# Understanding: Node Discovery

> Tor exit node fetching and database population

## Phase: EXPLORING

## Hypothesis

A background service that periodically fetches available Tor exit nodes from the official Onionoo API and populates a SQLite database for the API gateway to query.

## Sources

- `node_discovery.py` - Discovery script (103 lines)
- `docker/node-discovery/Dockerfile` - Container definition
- `docker-compose.yml:23-38` - Service definition

## Validated Understanding

### Core Functionality (`node_discovery.py`)

Standalone Python script that:
1. Fetches exit node data from Onionoo API
2. Filters and categorizes nodes by geography
3. Stores in SQLite for API consumption

#### Configuration

```python
ONIONOO_API_URL = "https://onionoo.torproject.org/details"
DB_PATH = "db/tor_nodes.db"
```

#### Database Schema

```sql
CREATE TABLE IF NOT EXISTS tor_nodes (
    fingerprint TEXT PRIMARY KEY,
    nickname TEXT,
    country TEXT,
    ip TEXT,
    is_exit INTEGER,
    is_running INTEGER,
    last_seen TEXT,
    geo_category TEXT,           -- "US" or "NON_US"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### Data Flow

1. **Fetch** - Query Onionoo API with filters:
   ```python
   params = {
       "flag": "Exit",           # Only exit relays
       "running": "true",        # Only active nodes
       "fields": "fingerprint,nickname,country,current_status,last_seen,or_addresses"
   }
   ```

2. **Process** - For each relay:
   - Extract IP from `or_addresses` (format: `["IP:PORT", ...]`)
   - Determine `geo_category`: `"US"` if country == "US", else `"NON_US"`
   - Skip if missing fingerprint, IP, or country

3. **Store** - Full refresh strategy:
   ```python
   cursor.execute("DELETE FROM tor_nodes")  # Clear all existing
   # Then insert fresh data
   ```

### Container Runtime

**Dockerfile**:
```dockerfile
FROM python:3.9-slim-buster
WORKDIR /app
COPY node_discovery.py .
RUN pip install requests
CMD ["bash", "-c", "while true; do python3 node_discovery.py; sleep 1800; done"]
```

**Behavior**:
- Runs discovery immediately on startup
- Repeats every 30 minutes (1800 seconds)
- No external orchestration needed

### Resource Constraints

```yaml
deploy:
  resources:
    limits:
      cpus: '0.25'
      memory: 64M
```

### Volume Sharing

- Writes to `db_data:/app/db`
- API service mounts same volume at `db_data:/app/db`
- Shared SQLite database access (potential concurrency consideration)

### Design Observations

1. **Full Refresh**: Deletes all nodes before inserting - no incremental updates
2. **No Health Tracking**: Doesn't track node health over time
3. **Simple Categorization**: Only US vs NON_US, no other geo options
4. **Error Handling**: Basic try/catch, prints errors but continues

## Children

| Child | Status | Rationale |
|-------|--------|-----------|
| [none] | - | Single-purpose script, no sub-concepts |

## Flow Recommendation

**Type**: SDD (Spec-Driven Development)

**Confidence**: HIGH

**Rationale**:
- Background data pipeline, internal infrastructure
- Clear data flow: API → Transform → Store
- No stakeholder-facing aspects

## Bubble Up

- **Purpose**: Populate SQLite with fresh Tor exit node data
- **Source**: Onionoo API (official Tor Project)
- **Schedule**: Every 30 minutes
- **Strategy**: Full refresh (delete all, insert all)
- **Categories**: US and NON_US exit nodes
- **Dependency**: Shared db_data volume with API

---

*Created by /legacy ENTERING phase*
*Updated by /legacy EXPLORING phase*
