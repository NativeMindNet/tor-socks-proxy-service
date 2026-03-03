# ADR-003: SQLite for Node Storage

## Meta
- **Number**: ADR-003
- **Type**: constraining
- **Status**: APPROVED
- **Created**: 2026-03-03
- **Decided**: 2026-03-03
- **Author**: /legacy analysis
- **Reviewers**: -

## Context

The node discovery service fetches Tor exit node data from the Onionoo API every 30 minutes. This data needs to be stored for the API service to query when creating new proxies. The storage solution must:

1. Be accessible by multiple services (node-discovery writes, api reads)
2. Support efficient queries by geo_category
3. Persist across container restarts
4. Be simple to deploy (no additional infrastructure)

## Decision Drivers

- Simplicity over scalability (thousands of records, not millions)
- No additional services to deploy/manage
- Easy volume sharing between containers
- SQL query support for filtering
- Single-writer scenario (only node-discovery writes)

## Considered Options

### Option 1: SQLite File Database

**Description**: Use SQLite database file stored in a shared Docker volume, accessed by both services.

**Pros**:
- Zero configuration (file-based)
- SQL support for queries
- Shared via Docker volume
- Atomic writes
- Built into Python stdlib

**Cons**:
- Single writer limitation
- No network access (file sharing required)
- Not suitable for high write concurrency

### Option 2: PostgreSQL/MySQL

**Description**: Deploy a dedicated database service in Docker Compose.

**Pros**:
- Full ACID compliance
- Network accessible
- Concurrent writers
- Rich query capabilities

**Cons**:
- Additional service to manage
- More complex deployment
- Overkill for ~3000 records
- Higher resource usage

### Option 3: Redis

**Description**: Use Redis for in-memory storage with persistence.

**Pros**:
- Very fast reads
- Network accessible
- Good for ephemeral data

**Cons**:
- Non-relational (harder queries)
- Memory-bound
- Additional service
- Less natural for tabular data

### Option 4: JSON File

**Description**: Write node data to a JSON file, read by API.

**Pros**:
- Simplest possible implementation
- Human readable
- No dependencies

**Cons**:
- No query capability
- Must load entire file
- No indexing
- Concurrent access issues

## Decision

We will use **Option 1: SQLite** because:

1. Perfect fit for single-writer, multiple-reader scenario
2. No additional infrastructure (just a file)
3. SQL queries enable efficient geo_category filtering
4. Built into Python (sqlite3 module)
5. Docker volume sharing is straightforward
6. Atomic writes prevent corruption during updates

## Consequences

### Positive
- Zero-infrastructure database
- SQL filtering (WHERE geo_category = ?)
- Primary key on fingerprint prevents duplicates
- Portable (just copy the .db file)
- Easy to inspect (`sqlite3` CLI)

### Negative
- Full refresh strategy required (DELETE all, INSERT all)
- No concurrent write support
- File locking during writes blocks reads momentarily
- Not suitable if data volume grows significantly

### Neutral
- Schema migrations would need manual handling
- No built-in replication

## Related Decisions
- ADR-002: Onionoo API - provides the data stored here

## Implementation References
- `node_discovery.py:9-27` - Database initialization
- `node_discovery.py:40-82` - Data insertion
- `api/main.py:89-105` - Database queries
- `docker-compose.yml` - db_data volume shared between services

## Tags
database storage sqlite persistence
