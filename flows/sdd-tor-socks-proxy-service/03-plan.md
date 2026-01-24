# Plan for Modernizing Socks-Proxy Project

This plan outlines the steps for refactoring the legacy `socks-proxy` project into a modern, modular, and containerized system. The refactoring will be executed in phases.

## Phase 1: Containerize Tor

The primary goal of this phase is to abstract Tor into a Docker container, making its deployment portable and removing reliance on hardcoded system paths.

### Tasks:

1.  **[x] Create a Dockerfile for Tor:**
    *   **Objective:** Define a Docker image that contains the Tor client and its necessary dependencies.
    *   **Details:**
        *   Start with a minimal base image (e.g., `alpine`, `debian-slim`).
        *   Install the `tor` package.
        *   Define a default `CMD` to start Tor.
        *   Expose the SOCKS port (default 9050).
        *   Ensure the image is lean and secure.
    *   **Deliverable:** `socks-proxy/docker/tor/Dockerfile`

2.  **[x] Create a Basic `docker-compose.yml` for a Single Tor Instance:**
    *   **Objective:** Demonstrate launching a single Tor container with a dynamically provided `torrc` file.
    *   **Details:**
        *   Define a service named `tor-proxy`.
        *   Use the Docker image created in Task 1.
        *   Map a host port to the container's SOCKS port (e.g., `9050:9050`).
        *   Mount a `torrc` file (initially a static test file) from the host into the container at the expected path (e.g., `/etc/tor/torrc`).
        *   Ensure the `torrc` file contains `SocksPort 0.0.0.0:9050` and `DataDirectory /var/lib/tor`.
    *   **Deliverable:** `socks-proxy/docker-compose.yml` (initial version)
    *   **Deliverable:** `socks-proxy/docker/tor/test.torrc` (a simple test `torrc` file)

3.  **[x] Verify Tor Container Functionality:**
    *   **Objective:** Confirm that the Tor container launches successfully and provides a functional SOCKS proxy.
    *   **Details:**
        *   Run `docker-compose up -d tor-proxy`.
        *   Check container logs (`docker-compose logs tor-proxy`).
        *   Verify proxy functionality by attempting to connect through it (e.g., using `curl --socks5-hostname localhost:9050 https://check.torproject.org/`).
    *   **Deliverable:** Confirmation of successful proxy operation.

## Phase 2: Modernize Tor Node Discovery

The primary goal of this phase is to replace the brittle CSV-based Tor node acquisition with a robust, reliable method using official Tor APIs and a persistent data store.

### Tasks:

1.  **[x] Identify Reliable Tor Node Data Source:**
    *   **Objective:** Confirm the use of Onionoo API as the primary source for Tor relay information.
    *   **Details:** Onionoo provides comprehensive, machine-readable data about Tor relays, including flags, country codes, IP addresses, and uptime.
    *   **Deliverable:** Confirmation of Onionoo API as the data source.

2.  **[x] Develop `node-discovery-service` (Python Script):**
    *   **Objective:** Create a Python script that fetches, parses, filters, and stores Tor relay data.
    *   **Details:**
        *   Use `requests` or `httpx` to query the Onionoo API (e.g., `https://onionoo.torproject.org/details?flag=Exit&running=true`).
        *   Parse the JSON response.
        *   Filter for running exit nodes (`Flag=Exit`, `Running=true`).
        *   Categorize nodes by geo-location (US vs. non-US) based on the `country` field.
        *   Store the relevant node information (e.g., IP, fingerprint, country, flags) into a simple SQLite database (`socks-proxy/db/tor_nodes.db`).
    *   **Deliverable:** `socks-proxy/node_discovery.py`
    *   **Deliverable:** `socks-proxy/db/tor_nodes.db` (initialized schema)

3.  **[x] Containerize `node-discovery-service`:**
    *   **Objective:** Create a Dockerfile for the `node-discovery-service` and integrate it into `docker-compose.yml`.
    *   **Details:**
        *   Create `socks-proxy/docker/node-discovery/Dockerfile`.
        *   Add a `node-discovery` service to `socks-proxy/docker-compose.yml`.
        *   Ensure the service can access the SQLite database (e.g., via a mounted volume for the `db` directory).
        *   Configure it to run periodically (e.g., using `cron` within the container or a simple `while true` loop with `sleep`).
    *   **Deliverable:** `socks-proxy/docker/node-discovery/Dockerfile`
    *   **Deliverable:** Updated `socks-proxy/docker-compose.yml`

## Phase 3: Develop the Control Plane API

The primary goal of this phase is to create a FastAPI-based REST API that allows programmatic control over the Tor proxy instances, enabling dynamic creation, management, and termination of geo-specific proxies.

### Tasks:

1.  **[x] Develop `tor-manager-api` (FastAPI Application):**
    *   **Objective:** Implement a Python API using FastAPI to manage proxy lifecycle.
    *   **Details:**
        *   Create `socks-proxy/api/main.py`.
        *   Initialize FastAPI app.
        *   Implement endpoint: `GET /proxies` to list active proxies.
        *   Implement endpoint: `POST /proxies` to create a new proxy.
        *   Implement endpoint: `DELETE /proxies/{port}` to terminate a proxy.
        *   Use Python's `docker` SDK to interact with the Docker daemon to start/stop Tor containers.
        *   Integrate with the SQLite database (`tor_nodes.db`) to select appropriate Tor exit nodes based on geo-category.
        *   Dynamically generate `torrc` files (in-memory or to a temporary location) for new Tor containers.
    *   **Deliverable:** `socks-proxy/api/main.py`
    *   **Deliverable:** `socks-proxy/api/requirements.txt` (for FastAPI, uvicorn, docker-py)

2.  **[x] Containerize `tor-manager-api`:**
    *   **Objective:** Create a Dockerfile for the API service and integrate it into `docker-compose.yml`.
    *   **Details:**
        *   Create `socks-proxy/docker/api/Dockerfile`.
        *   Add an `api` service to `socks-proxy/docker-compose.yml`.
        *   Map a host port (e.g., 8000) to the container's API port.
        *   Ensure the API container can access the `tor_nodes.db` (via a mounted volume) and the Docker daemon (e.g., by mounting `/var/run/docker.sock`).
        *   Make the `api` service depend on `node-discovery` to ensure node data is available.
    *   **Deliverable:** `socks-proxy/docker/api/Dockerfile`
    *   **Deliverable:** Updated `socks-proxy/docker-compose.yml`

3.  **[x] Implement `GET /proxies` Endpoint:**
    *   **Objective:** List currently managed proxy instances.
    *   **Details:** The API should query the Docker daemon for running Tor containers launched by the API and return their details (e.g., host port, geo-category).
    *   **Deliverable:** Implemented `GET /proxies` endpoint.

4.  **[x] Implement `POST /proxies` Endpoint:**
    *   **Objective:** Dynamically create and launch a new Tor proxy instance.
    *   **Details:**
        *   Accept a payload (e.g., `{"geo_category": "US", "fixed_ip_mode": "strict"}`).
        *   Query `tor_nodes.db` for an available exit node based on `geo_category`.
        *   Dynamically generate a `torrc` file for this specific node.
        *   Launch a new Tor container using the generated `torrc` and a dynamically assigned host port.
        *   Return the details of the newly created proxy (host port, exit IP, etc.).
    *   **Deliverable:** Implemented `POST /proxies` endpoint.

5.  **[x] Implement `DELETE /proxies/{port}` Endpoint:**
    *   **Objective:** Terminate a running Tor proxy instance.
    *   **Details:**
        *   Accept a host port as a path parameter.
        *   Identify the corresponding Tor container.
        *   Stop and remove the container.
        *   Return confirmation of termination.
    *   **Deliverable:** Implemented `DELETE /proxies/{port}` endpoint.

## Phase 4: Integrate and Deploy

The primary goal of this phase is to finalize the integration of all services and prepare for deployment, including considerations for monitoring and persistent storage.

### Tasks:

1.  **[x] Refine `docker-compose.yml` for Production Readiness:**
    *   **Objective:** Optimize the `docker-compose.yml` file for better performance, resource management, and reliability.
    *   **Details:**
        *   Ensure `restart: unless-stopped` is correctly applied to all services.
        *   Add resource limits (CPU, memory) for each service.
        *   Configure logging drivers if necessary (e.g., `json-file` with `max-size`, `max-file`).
        *   Add network definitions if services need to communicate over a custom network.
        *   Consider using named volumes for persistent data (e.g., `db` directory).
    *   **Deliverable:** Finalized `socks-proxy/docker-compose.yml`

2.  **[x] Implement Basic API Health Checks and Monitoring:**
    *   **Objective:** Provide basic health checks for the API and consider metrics for monitoring.
    *   **Details:**
        *   The `GET /health` endpoint is already a good start.
        *   Consider integrating Prometheus metrics (e.g., `fastapi-prometheus` library) to expose API request counts, latencies, etc.
        *   Consider adding health checks to `docker-compose.yml` for services.
    *   **Deliverable:** Enhanced API health checks and basic monitoring setup.

3.  **[x] Deployment Documentation:**
    *   **Objective:** Provide clear instructions on how to deploy and manage the modernized system.
    *   **Details:**
        *   Write a `README.md` for the `socks-proxy` directory.
        *   Include steps to build images, run `docker-compose`, interact with the API, and shut down.
        *   Explain how to configure persistent storage for the database.
    *   **Deliverable:** `socks-proxy/README.md`

4.  **[x] Cleanup Legacy Components:**
    *   **Objective:** Remove old PHP scripts and shell scripts related to the legacy proxy management.
    *   **Details:**
        *   Delete `socks-proxy/run/all.sh`, `socks-proxy/run/ru/`, `socks-proxy/run/nonru/`, `socks-proxy/run/make.php`, `socks-proxy/run/make2.php`, `socks-proxy/run/makeswap.sh`, `socks-proxy/run/torrc`, `socks-proxy/scripts/script.php`, etc.
        *   Ensure no dependency on these old files remains.
    *   **Deliverable:** Cleaned `socks-proxy/` directory

## Phase 6: Implement CI/CD (GitHub Actions)

The goal of this phase is to automate validation and build processes.

### Tasks:

1.  **[ ] Create GitHub Actions Workflow File:**
    *   **Objective:** Define the CI/CD pipeline in `.github/workflows/tor-socks-proxy-ci.yml`.
    *   **Details:** Configure triggers, linting steps (Ruff), and Docker build checks.
    *   **Deliverable:** `.github/workflows/tor-socks-proxy-ci.yml`

2.  **[ ] Add Python Linting and Static Analysis:**
    *   **Objective:** Ensure code quality and security.
    *   **Details:** Add steps to run `ruff` for linting and `bandit` for security scanning.
    *   **Deliverable:** Updated workflow file.

3.  **[ ] Add Docker Build Verification:**
    *   **Objective:** Ensure that all Docker images build correctly.
    *   **Details:** Add a step that runs `docker-compose build` within the GitHub Action environment.
    *   **Deliverable:** Updated workflow file.

4.  **[ ] (Optional) Add Basic Smoke Test:**
    *   **Objective:** Verify the API starts up correctly in CI.
    *   **Details:** Start containers and hit the `/health` endpoint.
    *   **Deliverable:** Updated workflow file.

## Phase 7: Implement Monitoring Stack

The goal of this phase is to provide real-time visibility into the system.

### Tasks:

1.  **[ ] Instrument FastAPI Application:**
    *   **Objective:** Export API and custom metrics for Prometheus.
    *   **Details:** 
        *   Add `prometheus-fastapi-instrumentator` to `api/requirements.txt`.
        *   Configure the instrumentator in `api/main.py`.
        *   Implement custom gauges for active proxy counts.
    *   **Deliverable:** Instrumented `api/main.py`

2.  **[ ] Integrate Prometheus and cAdvisor:**
    *   **Objective:** Set up metrics collection.
    *   **Details:**
        *   Add `prometheus` and `cadvisor` services to `docker-compose.yml`.
        *   Create `socks-proxy/monitoring/prometheus.yml` with scrape configurations.
    *   **Deliverable:** Updated `docker-compose.yml` and prometheus config.

3.  **[ ] Integrate Grafana:**
    *   **Objective:** Set up visualization.
    *   **Details:**
        *   Add `grafana` service to `docker-compose.yml`.
        *   Configure Prometheus as a default data source.
    *   **Deliverable:** Updated `docker-compose.yml` with Grafana.

4.  **[ ] Create Dashboards:**
    *   **Objective:** Visualize the system state.
    *   **Details:** Create JSON definitions or manually configure the three core dashboards (Control Plane, Tor Nodes, Infrastructure).
    *   **Deliverable:** Grafana dashboard definitions.


