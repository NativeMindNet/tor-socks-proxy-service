This document outlines the specifications for enhancing the existing socks-proxy system to provide different proxies with fixed outgoing IPs based on port, and considering US and NON-US geo-locations.

## Current System Overview:
The existing `socks-proxy` system is located in the `socks-proxy/` directory within the project. It uses Tor for proxy functionality and a PHP script (`socks-proxy/run/make.php`) for orchestration.

### Key Components:
-   **`socks-proxy/run/all.sh`**: Main entry point, responsible for cleaning Tor data and launching geo-specific `start.sh` scripts.
-   **`socks-proxy/run/ru/start.sh` & `socks-proxy/run/nonru/start.sh`**: Scripts that launch multiple Tor instances, each using a `torrc` configuration file located in `/etc/tor/`.
-   **`socks-proxy/run/make.php`**: The core configuration generator.
    -   Fetches Tor relay information from `http://torstatus.rueckgr.at/query_export.php/Tor_query_EXPORT.csv`.
    -   Filters relays into "RU" and "nonRU" groups (excluding "UA" and "CH").
    -   Assigns a local SOCKS port to each group of exit nodes based on an IP hash.
    -   Generates individual `torrc` configuration files from a template (`socks-proxy/run/torrc`) into `socks-proxy/run/res/`. These `torrc` files define `SocksPort`, `DataDirectory`, and critically, `ExitNodes` set to a list of `/16` CIDR ranges.
    -   Generates `start.sh` scripts (for `ru/` and `nonru/`) which *expect* the `torrc` files to be in `/etc/tor/`.
-   **`socks-proxy/run/torrc`**: The template `torrc` file used by `make.php`.
-   **`socks-proxy/run/res/`**: Directory where `make.php` outputs generated `torrc` files.
-   **Discrepancy**: There is a mismatch between where `make.php` writes `torrc` files (`socks-proxy/run/res/`) and where `start.sh` scripts expect them (`/etc/tor/`). This implies an external copying process or manual intervention.

## Proposed Enhancements:

The goal is to modify the system to provide different SOCKS5 proxies, each listening on a unique port, with configurable outgoing geo-location (US or NON-US) and a more controlled "fixed" outgoing IP (or a tightly controlled set of IPs).

### A. Core Mechanism for Geo-location and Port Assignment:

1.  **Refine Geo-filtering in `socks-proxy/run/make.php`:**
    *   **Current State:** Filters for "RU" and "nonRU" (`$sel_a = array("RU", "!RU");`).
    *   **Modification:**
        *   Change `$sel_a` array to include "US" and "NON_US" categories (e.g., `array("US", "NON_US")`).
        *   Update the country filtering logic within the `foreach($nodes as $node)` loop to correctly categorize nodes as "US" or "NON_US".
        *   **Example Logic:**
            ```php
            if ($sel == "US") {
                // Node must be from the US
                if ($country != "US") continue;
            } else { // $sel == "NON_US"
                // Node must NOT be from the US, and optionally exclude other specific countries
                if ($country == "US" || $country == "UA" || $country == "CH") continue;
            }
            // Ensure only good exit nodes are selected
            if (!(($FlagExit=="1")&&($FlagBadExit=="0"))) continue;
            ```
2.  **Create new Geo-specific Output Directories:**
    *   Modify `make.php` to output `exits.csv`, `ports.csv`, and `start.sh` files into new `socks-proxy/run/us/` and `socks-proxy/run/nonus/` subdirectories.

3.  **Port Allocation Strategy for "Fixed IP":**
    *   **Option 1: Grouped IPs per Port (Recommended for Robustness)**
        *   **Behavior:** Each local SOCKS port will route traffic through *any* available Tor exit node within a specified `/16` CIDR range. The exit IP will vary within that range, offering a balance between "fixed geo" and Tor's design.
        *   **Implementation:** Retain the current IP-hashing port assignment logic (`$port = ($h)%64000+1535;`). The `ExitNodes` in the `torrc` will continue to be a list of `/16` CIDR ranges, but now *geo-filtered* (US or NON-US).
    *   **Option 2: Single Fixed IP per Port (Higher Granularity, Lower Reliability)**
        *   **Behavior:** Each local SOCKS port attempts to route traffic through a *single, specific* Tor exit node (identified by IP or fingerprint). This provides the highest degree of "fixed IP" control but increases fragility if that specific node goes offline.
        *   **Implementation:**
            *   Modify `make.php` to assign a unique local SOCKS port for *each individual US exit IP* and *each individual NON-US exit IP* that passes the filtering criteria.
            *   Modify the `maketorconf` section in `make.php` to set `ExitNodes` to the *single IP address* (e.g., `$iexits = $ip;` instead of `implode($nets,",");`) for that specific port.
            *   Consider using Tor relay fingerprints as `ExitNodes` if available and preferred for stability over dynamic IP addresses.

### B. Bridging the Path Discrepancy:

1.  **Problem:** `make.php` writes generated `torrc` files to `socks-proxy/run/res/`, but the generated `start.sh` scripts (and the existing system's behavior) expect them to be in `/etc/tor/`.
2.  **Solution:**
    *   Modify `socks-proxy/run/all.sh` to include a step that copies the `torrc` files from `socks-proxy/run/res/` to `/etc/tor/`.
    *   Ensure proper permissions are set for the copied files.
    *   **Example addition to `socks-proxy/run/all.sh` (before calling `start.sh`):**
        ```bash
        # ... (existing cleanup and mkdir for /var/lib/tor) ...

        # Ensure /etc/tor exists and has correct permissions
        sudo mkdir -p /etc/tor
        # Copy generated torrc files to /etc/tor/
        sudo cp /home/anton/proj/nanolocalproxy/run/res/torrc.* /etc/tor/
        sudo chmod 0644 /etc/tor/torrc.*

        # ... (existing calls to start.sh for ru/ and nonru/) ...
        ```
        *(Note: The absolute path `/home/anton/proj/nanolocalproxy/` is assumed to be the effective base path of the `socks-proxy` directory on the execution system.)*

## Changes to Existing Files:

*   `socks-proxy/run/make.php` (Core modification for geo-filtering, port assignment, and ExitNodes generation).
*   `socks-proxy/run/all.sh` (Update paths for `start.sh` and add `torrc` copying logic).

## New Directories:

*   `socks-proxy/run/us/`
*   `socks-proxy/run/nonus/`

## Considerations:

*   **Tor Node Reliability:** Tor exit nodes are dynamic. Relying on truly fixed individual IPs (Option 2) can lead to service instability if the specified node goes offline. Grouped IPs (Option 1) are more resilient.
*   **Performance:** Running a large number of Tor instances can consume significant system resources (CPU, RAM, network).
*   **Security:** Ensure proper isolation between different Tor instances and secure management of the proxy system.

## Acceptance Criteria:

*   When `socks-proxy/run/all.sh` is executed, Tor SOCKS proxies are launched.
*   Proxies for "US" geo-location are available on a defined set of ports (e.g., `us/start.sh`).
*   Proxies for "NON-US" geo-location are available on a defined set of ports (e.g., `nonus/start.sh`).
*   Each proxy's `torrc` configuration accurately reflects the intended `ExitNodes` for its geo-category and desired fixed-IP granularity.
*   No manual copying of `torrc` files is required after running `make.php`.

## CI/CD Pipeline Specification (GitHub Actions)

A GitHub Actions workflow will be created in `.github/workflows/tor-socks-proxy.yml` to automate the following:

1.  **Trigger:**
    *   Push to `main` branch.
    *   Pull requests targeting `main`.
    *   Changes specifically within the `socks-proxy/` directory.

2.  **Jobs:**
    *   **Linting:**
        *   Run `ruff` or `flake8` on Python files (`api/main.py`, `node_discovery.py`).
        *   Check for security issues using `bandit`.
    *   Build & Test:
        *   Verify that `docker-compose build` completes successfully.
        *   (Optional) Run a basic smoke test by starting the services and checking the `/health` endpoint.
    *   **Docker Hub (Optional/Future):**
        *   Build and push images to a registry if configured.

## Monitoring & Observability Specification

The monitoring stack will be integrated into the `docker-compose.yml` to provide real-time visibility.

### 1. Architecture
*   **Prometheus:** Central time-series database for collecting metrics.
*   **Grafana:** Visualization tool for dashboards.
*   **cAdvisor:** Container metrics exporter (CPU, Memory, Network per container).
*   **FastAPI Instrumentation:** `prometheus-fastapi-instrumentator` will be added to the API to export HTTP metrics (RPS, Latency, Errors).

### 2. Metrics to Collect
*   **API Metrics:** `http_requests_total`, `http_request_duration_seconds`.
*   **Proxy Metrics:** Custom gauge for `active_proxy_containers` (labeled by geo_category).
*   **Discovery Metrics:** Custom gauge for `available_tor_exit_nodes` (labeled by geo_category).
*   **System Metrics:** Container CPU, Memory, and Network I/O.

### 3. Dashboard Designs

#### A. Control Plane & API Health
*   **Active Proxies:** Total count and geo-distribution (Pie Chart).
*   **API Load:** Requests per second and response time (Latency).
*   **HTTP Success Rate:** Ratio of 2xx vs 4xx/5xx errors.

#### B. Tor Node Intelligence
*   **Database Capacity:** Number of US vs NON-US nodes in `tor_nodes.db`.
*   **Update Freshness:** Time since last discovery run.

#### C. Infrastructure & Resources
*   **Resource Consumption:** CPU and Memory usage per service and per individual Tor container.
*   **Traffic Volume:** Network throughput for the entire proxy gateway.