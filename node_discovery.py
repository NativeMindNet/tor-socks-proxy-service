import requests
import sqlite3
import time
import os

ONIONOO_API_URL = "https://onionoo.torproject.org/details"
DB_PATH = "db/tor_nodes.db"

def initialize_db(db_path):
    """Initializes the SQLite database schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tor_nodes (
            fingerprint TEXT PRIMARY KEY,
            nickname TEXT,
            country TEXT,
            ip TEXT,
            is_exit INTEGER,
            is_running INTEGER,
            last_seen TEXT,
            geo_category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def fetch_tor_nodes():
    """Fetches Tor relay details from the Onionoo API."""
    params = {
        "flag": "Exit",
        "running": "true",
        "fields": "fingerprint,nickname,country,current_status,last_seen,or_addresses"
    }
    response = requests.get(ONIONOO_API_URL, params=params, timeout=30)
    response.raise_for_status() # Raise an exception for HTTP errors
    return response.json()

def process_and_store_nodes(nodes_data, db_path):
    """Processes fetched nodes and stores them in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing nodes to get a fresh list
    cursor.execute("DELETE FROM tor_nodes")

    for relay in nodes_data.get("relays", []):
        fingerprint = relay.get("fingerprint")
        nickname = relay.get("nickname")
        country = relay.get("country")
        
        # 'current_status' is a list like ["running"]
        is_running = 1 if "running" in relay.get("current_status", []) else 0
        is_exit = 1 # Already filtered by API for Exit flag
        last_seen = relay.get("last_seen")
        
        # Extract IP address. Onionoo returns a list of OR addresses.
        # We'll take the first one or None if not available.
        ip = None
        if relay.get("or_addresses"):
            # or_addresses format: ["<IP>:<PORT>", ...]
            first_address = relay["or_addresses"][0]
            ip = first_address.split(":")[0]

        if not (fingerprint and ip and country):
            continue # Skip if essential info is missing

        geo_category = "US" if country and country.upper() == "US" else "NON_US"

        try:
            cursor.execute("""
                INSERT INTO tor_nodes (fingerprint, nickname, country, ip, is_exit, is_running, last_seen, geo_category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fingerprint, nickname, country, ip, is_exit, is_running, last_seen, geo_category))
        except sqlite3.IntegrityError:
            print(f"Skipping duplicate fingerprint: {fingerprint}")
        except Exception as e:
            print(f"Error inserting node {fingerprint}: {e}")

    conn.commit()
    conn.close()
    print(f"Stored {len(nodes_data.get('relays', []))} nodes to database.")

def main():
    db_dir = os.path.dirname(DB_PATH)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
        
    initialize_db(DB_PATH)
    print("Fetching Tor node data...")
    try:
        nodes_data = fetch_tor_nodes()
        process_and_store_nodes(nodes_data, DB_PATH)
        print("Tor node discovery completed successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Onionoo API: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
