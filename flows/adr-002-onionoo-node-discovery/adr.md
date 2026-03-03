# ADR-002: Onionoo API for Node Discovery

## Meta
- **Number**: ADR-002
- **Type**: enabling
- **Status**: APPROVED
- **Created**: 2026-03-03
- **Decided**: 2026-03-03
- **Author**: /legacy analysis
- **Reviewers**: -

## Context

The legacy socks-proxy system fetched Tor relay information from a third-party CSV export endpoint (`http://torstatus.rueckgr.at/query_export.php/Tor_query_EXPORT.csv`). This approach had several problems:

1. **Unreliable source**: Third-party service with no SLA
2. **Stale data**: CSV was not always current
3. **Parsing complexity**: CSV format required custom parsing
4. **Limited fields**: Not all relay metadata was available
5. **Single point of failure**: If the service went down, node discovery failed

The modernized system needed a reliable, official source of Tor relay data with rich metadata for filtering.

## Decision Drivers

- Need authoritative source for Tor exit node data
- Require current/active relay status
- Must have country/geo information for filtering
- Need relay fingerprints for stable identification
- Should be machine-readable (JSON preferred)

## Considered Options

### Option 1: Third-party CSV Export (Legacy)

**Description**: Continue using torstatus.rueckgr.at or similar third-party aggregators.

**Pros**:
- Already implemented
- Simple HTTP GET + CSV parsing
- No authentication required

**Cons**:
- Third-party service (no guarantees)
- Data freshness unknown
- CSV parsing is fragile
- May disappear without notice

### Option 2: Onionoo API (Tor Project)

**Description**: Use the official Onionoo API provided by the Tor Project at `https://onionoo.torproject.org/`.

**Pros**:
- Official Tor Project service
- JSON response (easy parsing)
- Rich filtering options (flags, running, country)
- Comprehensive relay metadata
- Maintained long-term
- Free and unauthenticated

**Cons**:
- Rate limiting possible (though generous)
- Larger response payloads than CSV

### Option 3: Direct Tor Consensus Parsing

**Description**: Fetch and parse the raw Tor network consensus directly from directory authorities.

**Pros**:
- Most authoritative source possible
- Real-time data
- No third-party dependency

**Cons**:
- Complex consensus parsing
- Requires cryptographic verification
- Significantly more implementation effort
- Must track multiple directory authorities

## Decision

We will use **Option 2: Onionoo API** because:

1. Official Tor Project service with long-term maintenance commitment
2. JSON format with built-in filtering eliminates parsing complexity
3. Rich metadata includes everything needed (fingerprint, IP, country, flags)
4. Server-side filtering (e.g., `?flag=Exit&running=true`) reduces bandwidth
5. Free, unauthenticated, and well-documented

## Consequences

### Positive
- Reliable, authoritative data source
- Simple JSON parsing with Python `requests`
- Server-side filtering reduces response size
- All needed metadata in one call
- Active nodes only (`running=true` filter)

### Negative
- Internet connectivity required for updates
- Depends on Tor Project infrastructure
- Full node list can be large (~3000+ exit nodes)

### Neutral
- Discovery runs periodically (30 min) regardless of API choice
- Node data structure adapts to Onionoo's schema

## Related Decisions
- ADR-003: SQLite for Node Storage - stores data fetched from Onionoo

## Implementation References
- `node_discovery.py:6` - API URL constant
- `node_discovery.py:29-38` - fetch_tor_nodes() with filters
- `node_discovery.py:40-82` - Response processing

## Tags
api tor network discovery external-service
