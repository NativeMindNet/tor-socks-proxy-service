# Requirements - tor-socks-proxy

## Problem Statement
The legacy `socks-proxy` system is brittle, relying on complex PHP and shell scripts, manual file copying, and outdated Tor node discovery methods. It lacks a modern API for dynamic proxy management and is difficult to deploy and scale.

## Goals
- **Containerization:** Move Tor instances into Docker containers for isolation and portability.
- **Modern Discovery:** Use the Onionoo API for reliable Tor node discovery instead of static CSV files.
- **REST API:** Provide a FastAPI-based interface to dynamically create, list, and destroy proxies.
- **Geo-Filtering:** Enable selection of exit nodes based on geo-location (US vs. NON-US).
- **Fixed IP Support:** Provide options for "strict" (single IP) or "flexible" (grouped IPs) proxy modes.
- **CI/CD:** Implement GitHub Actions for automated linting, testing, and Docker image building.
- **Monitoring & Observability:** Provide real-time visibility into API health, proxy lifecycle, Tor node pool status, and container resource usage using Prometheus and Grafana.

## User Stories
- **As a developer**, I want to request a US-based proxy via an API call so that I can perform geo-restricted scraping.
- **As a system administrator**, I want the Tor node list to be updated automatically so that the proxies always use active and healthy exit nodes.
- **As a developer**, I want to be able to spin up and tear down multiple proxies programmatically without manual configuration.
- **As a contributor**, I want my changes to be automatically tested and validated via GitHub Actions before they are merged.
- **As an operator**, I want to see a dashboard showing how many proxies are active and if the system is running out of resources.

## Acceptance Criteria
- [x] Tor is successfully containerized and can be launched with custom `torrc` files.
- [x] A background service automatically populates an SQLite database with fresh Tor exit nodes.
- [x] API endpoints exist for:
    - `POST /proxies`: Create a new proxy with specified `geo_category`.
    - `GET /proxies`: List all active proxies.
    - `DELETE /proxies/{port}`: Terminate a specific proxy.
- [x] Legacy PHP and shell scripts are removed.
- [x] System is deployable via `docker-compose`.
- [x] GitHub Actions workflow is implemented for:
    - [x] Linting Python code (e.g., using `flake8` or `ruff`).
    - [x] Running unit tests (if applicable).
    - [x] Building and tagging Docker images on push to main.
- [ ] Monitoring stack (Prometheus, Grafana, cAdvisor) is integrated into `docker-compose`.
- [ ] FastAPI application exports metrics in Prometheus format.
- [ ] Grafana dashboards are provided for:
    - Control Plane (API & Proxy counts).
    - Tor Node Intelligence (DB status).
    - Infrastructure (CPU/RAM/Network).

## Constraints & Non-Goals
- **Non-Goal:** Replacing Tor with another proxy technology.
- **Constraint:** Must run on systems with Docker and Docker Compose.
