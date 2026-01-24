# Tor Proxy Manager

This project provides a modernized, containerized solution for managing multiple Tor SOCKS5 proxy instances with geo-specific exit nodes, replacing a legacy PHP and shell script-based system.

## Features

-   **Dynamic Proxy Creation:** Spin up new Tor proxies on demand via a REST API.
-   **Geo-Specific Exit Nodes:** Request proxies with US or NON-US exit nodes.
-   **Containerized Tor Instances:** Each proxy runs in an isolated Docker container.
-   **Automated Node Discovery:** Periodically fetches and updates Tor exit node information from the Onionoo API.
-   **API-Driven Control:** Manage proxies programmatically via a FastAPI application.
-   **Production-Ready Deployment:** Uses Docker Compose for orchestration, with resource limits, logging, and health checks.

## Architecture

The system consists of three main services orchestrated by Docker Compose:

1.  **`node-discovery`**: A Python service that fetches fresh Tor exit node data from the Onionoo API and stores it in an SQLite database.
2.  **`api`**: A FastAPI application that provides a REST API to manage Tor proxy instances. It interacts with the Docker daemon to create and destroy Tor containers, using data from the `node-discovery` service.
3.  **`tor-proxy`**: A Docker image for running individual Tor SOCKS5 proxy instances. These containers are dynamically launched by the `api` service.

## Getting Started

### Prerequisites

-   Docker and Docker Compose installed on your system.
-   `curl` or a similar tool for testing the API.

### 1. Build Docker Images

Navigate to the `socks-proxy` directory and build the Docker images:

```bash
cd socks-proxy
docker-compose build
```

### 2. Start Services

Start the `node-discovery` and `api` services. The `tor-proxy` service in `docker-compose.yml` is an example for testing; dynamic proxies are launched by the API.

```bash
docker-compose up -d node-discovery api
```
*(Optional: `docker-compose up -d` to start all services including the test `tor-proxy`)*

Wait a few minutes for the `node-discovery` service to fetch Tor node data and populate the database, and for the `api` service to start up.

### 3. Verify Service Health

You can check the health of the API service:

```bash
curl http://localhost:8000/health
```
Expected output: `{"status":"ok","docker_connected":true}`

You can also inspect the logs of any service:

```bash
docker-compose logs node-discovery
docker-compose logs api
```

### 4. Interact with the API

The API runs on `http://localhost:8000`. You can use the interactive API documentation at `http://localhost:8000/docs`.

#### Create a US Proxy

```bash
curl -X POST "http://localhost:8000/proxies" \
     -H "Content-Type: application/json" \
     -d '{"geo_category": "US", "fixed_ip_mode": "flexible"}'
```
This will return details of the new proxy, including the host port it's listening on.

#### Create a NON-US Proxy

```bash
curl -X POST "http://localhost:8000/proxies" \
     -H "Content-Type: application/json" \
     -d '{"geo_category": "NON_US", "fixed_ip_mode": "flexible"}'
```

#### List Active Proxies

```bash
curl http://localhost:8000/proxies
```
This will show all Tor proxy containers currently managed by the API.

#### Test a Proxy (e.g., on host port 12345)

Replace `12345` with the `port` returned by the `POST /proxies` call.

```bash
curl --socks5-hostname localhost:12345 https://check.torproject.org/
```
You should see confirmation that you are using Tor, and the exit IP should match the geo-category requested.

#### Terminate a Proxy (e.g., on host port 12345)

```bash
curl -X DELETE "http://localhost:8000/proxies/12345"
```

### 5. Persistent Storage for Database

The SQLite database (`tor_nodes.db`) is stored in a Docker named volume called `db_data`. This ensures that your Tor node data persists even if containers are removed.

-   **Volume Location:** Docker manages named volumes. You can inspect its location using `docker volume inspect db_data`.
-   **Backup/Restore:** You can back up the `db_data` volume or its contents as needed.

## Shutting Down

To stop and remove all services and the named volume:

```bash
docker-compose down -v
```
To stop services without removing the volume:

```bash
docker-compose down
```

## Development Notes

-   **Hot Reloading:** The `api` and `node-discovery` services are configured to mount their respective Python scripts and `requirements.txt`. This allows for easier development as changes to these files will be reflected upon container restart or `uvicorn`'s hot-reloading (for the API).
-   **Docker Socket:** The `api` service mounts `/var/run/docker.sock` to interact with the Docker daemon. Ensure your user has permissions to access this socket.
