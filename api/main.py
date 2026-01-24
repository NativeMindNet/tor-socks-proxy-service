from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import sqlite3
import docker
import random
import os
import time
import json
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge

# --- Configuration ---
DB_PATH = "/app/db/tor_nodes.db"
TOR_IMAGE_NAME = "tor-proxy-image:latest"
API_HOST_PORT = 8000
CONFIGS_INTERNAL_PATH = "/etc/tor_configs"
CONFIGS_VOLUME_NAME = "socks-proxy_tor_configs_data"

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Tor Proxy Manager API",
    description="API to dynamically manage Tor proxy instances with geo-specific exit nodes."
)

# --- Metrics Configuration ---
active_proxies_gauge = Gauge(
    "tor_proxy_manager_active_proxies",
    "Number of active Tor proxy containers",
    ["geo_category"]
)

available_nodes_gauge = Gauge(
    "tor_proxy_manager_available_exit_nodes",
    "Number of available Tor exit nodes in database",
    ["geo_category"]
)

def update_custom_metrics():
    """Updates custom Prometheus gauges for proxies and nodes."""
    if not client:
        return

    # Update Active Proxies Gauge
    us_count = 0
    non_us_count = 0
    try:
        for container in client.containers.list():
            if container.name.startswith("tor-proxy-"):
                proxy_info_str = container.labels.get("com.example.proxy_info")
                if proxy_info_str:
                    proxy_info = json.loads(proxy_info_str)
                    geo = proxy_info.get("geo_category")
                    if geo == "US":
                        us_count += 1
                    elif geo == "NON_US":
                        non_us_count += 1
    except Exception as e:
        print(f"Error updating active proxies gauge: {e}")
    
    active_proxies_gauge.labels(geo_category="US").set(us_count)
    active_proxies_gauge.labels(geo_category="NON_US").set(non_us_count)

    # Update Available Nodes Gauge
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT geo_category, COUNT(*) as count FROM tor_nodes GROUP BY geo_category")
        rows = cursor.fetchall()
        
        # Reset counts in case some categories are missing from DB
        available_nodes_gauge.labels(geo_category="US").set(0)
        available_nodes_gauge.labels(geo_category="NON_US").set(0)
        
        for row in rows:
            available_nodes_gauge.labels(geo_category=row["geo_category"]).set(row["count"])
        conn.close()
    except Exception as e:
        print(f"Error updating available nodes gauge: {e}")

# --- Docker Client Initialization ---
try:
    client = docker.from_env()
    client.ping()
except Exception as e:
    print(f"Could not connect to Docker daemon: {e}")
    client = None

# --- Database Helper ---
def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run node_discovery.py first.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_random_exit_node(geo_category: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT fingerprint, ip, country FROM tor_nodes WHERE geo_category = ? ORDER BY RANDOM() LIMIT 1",
        (geo_category,)
    )
    node = cursor.fetchone()
    conn.close()
    return node

# --- Torrc Generation Helper ---
def generate_torrc(socks_port: int, exit_node_ip: str = None, exit_node_fingerprint: str = None) -> str:
    torrc_content = f"""
SocksPort 0.0.0.0:{socks_port}
DataDirectory /var/lib/tor
Log notice stdout
ClientOnly 1
StrictNodes 1
"""
    if exit_node_ip:
        torrc_content += f"ExitNodes {exit_node_ip}\n"
        torrc_content += f"ExitRelay 0\n"
    elif exit_node_fingerprint:
        torrc_content += f"ExitNodes {exit_node_fingerprint}\n"
        torrc_content += f"ExitRelay 0\n"
    
    return torrc_content.strip()

# --- Data Models for API Requests ---
class CreateProxyRequest(BaseModel):
    geo_category: str # "US" or "NON_US"
    fixed_ip_mode: str = "flexible" # "flexible" or "strict"

class ProxyInfo(BaseModel):
    port: int
    geo_category: str
    exit_ip: str
    fingerprint: str
    container_id: str
    status: str

# --- API Endpoints ---

@app.on_event("startup")
def startup_event():
    # Initialize instrumentation
    Instrumentator().instrument(app).expose(app)
    
    if client:
        print("Successfully connected to Docker daemon.")
        update_custom_metrics()
    else:
        print("Warning: Docker daemon not connected.")

@app.get("/proxies", response_model=list[ProxyInfo])
def list_proxies():
    running_proxies = []
    if not client:
        return []
    
    for container in client.containers.list():
        # Check if it's one of our proxy containers
        if container.name.startswith("tor-proxy-"):
            try:
                proxy_info_str = container.labels.get("com.example.proxy_info")
                if proxy_info_str:
                    proxy_info = json.loads(proxy_info_str)
                    ports = container.ports
                    host_port = None
                    if '9050/tcp' in ports and ports['9050/tcp']:
                        host_port = int(ports['9050/tcp'][0]['HostPort'])
                    
                    if host_port:
                        running_proxies.append(ProxyInfo(
                            port=host_port,
                            geo_category=proxy_info.get("geo_category", "unknown"),
                            exit_ip=proxy_info.get("exit_ip", "unknown"),
                            fingerprint=proxy_info.get("fingerprint", "unknown"),
                            container_id=container.id,
                            status=container.status
                        ))
            except Exception as e:
                print(f"Error parsing proxy_info for container {container.id}: {e}")
    
    return running_proxies

@app.post("/proxies", response_model=ProxyInfo)
def create_proxy(request: CreateProxyRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Docker daemon not connected.")

    exit_node = get_random_exit_node(request.geo_category)
    if not exit_node:
        raise HTTPException(status_code=404, detail=f"No {request.geo_category} exit nodes found.")

    selected_ip = exit_node["ip"]
    selected_fingerprint = exit_node["fingerprint"]

    torrc_content = generate_torrc(
        socks_port=9050, 
        exit_node_ip=selected_ip if request.fixed_ip_mode == "strict" else None,
        exit_node_fingerprint=selected_fingerprint if request.fixed_ip_mode != "strict" else None
    )

    container_id_short = selected_fingerprint[:12]
    timestamp = int(time.time())
    config_filename = f"torrc_{container_id_short}_{timestamp}"
    config_file_path = os.path.join(CONFIGS_INTERNAL_PATH, config_filename)
    container_name = f"tor-proxy-{container_id_short}-{timestamp}"

    try:
        with open(config_file_path, "w") as f:
            f.write(torrc_content)
        os.chmod(config_file_path, 0o644)

        container = client.containers.run(
            image=TOR_IMAGE_NAME,
            detach=True,
            ports={'9050/tcp': None},
            volumes={CONFIGS_VOLUME_NAME: {'bind': CONFIGS_INTERNAL_PATH, 'mode': 'ro'}},
            command=["tor", "-f", f"{CONFIGS_INTERNAL_PATH}/{config_filename}"],
            name=container_name,
            remove=True,
            labels={
                "com.example.proxy_info": json.dumps({
                    "geo_category": request.geo_category,
                    "exit_ip": selected_ip,
                    "fingerprint": selected_fingerprint,
                })
            }
        )
        
        time.sleep(2)
        container.reload()
        
        host_port = None
        if '9050/tcp' in container.ports and container.ports['9050/tcp']:
            host_port = int(container.ports['9050/tcp'][0]['HostPort'])
        
        if not host_port or container.status != 'running':
            logs = container.logs().decode('utf-8')
            raise HTTPException(status_code=500, detail=f"Proxy container failed to start. Logs: {logs[:100]}...")

        update_custom_metrics()
        return ProxyInfo(
            port=host_port,
            geo_category=request.geo_category,
            exit_ip=selected_ip,
            fingerprint=selected_fingerprint,
            container_id=container.id,
            status=container.status
        )

    except Exception as e:
        if os.path.exists(config_file_path):
            os.remove(config_file_path)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Failed to create proxy: {str(e)}")

@app.delete("/proxies/{port}", response_model=dict)
def delete_proxy(port: int):
    if not client:
        raise HTTPException(status_code=500, detail="Docker daemon not connected.")

    target_container = None
    for container in client.containers.list():
        ports = container.ports
        if '9050/tcp' in ports and ports['9050/tcp']:
            if int(ports['9050/tcp'][0]['HostPort']) == port:
                target_container = container
                break
    
    if not target_container:
        raise HTTPException(status_code=404, detail=f"Proxy on port {port} not found.")

    try:
        cmd = target_container.attrs['Config']['Cmd']
        if len(cmd) >= 3 and cmd[1] == '-f':
            config_path = cmd[2]
            if os.path.exists(config_path):
                os.remove(config_path)

        target_container.stop()
        update_custom_metrics()
        return {"message": f"Proxy on port {port} terminated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to terminate proxy: {e}")

@app.get("/health")
def health_check():
    update_custom_metrics() # Refresh metrics on health check as well
    return {"status": "ok", "docker_connected": bool(client)}

if __name__ == "__main__":
    import uvicorn
    if not os.path.exists(CONFIGS_INTERNAL_PATH):
        os.makedirs(CONFIGS_INTERNAL_PATH)
    uvicorn.run(app, host="0.0.0.0", port=API_HOST_PORT)
