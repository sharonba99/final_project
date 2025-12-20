import os
import random
import string
import psycopg2
from psycopg2 import pool, extras
from flask import Flask, request, jsonify, redirect, abort
from flask_cors import CORS
from prometheus_client import Counter, generate_latest

app = Flask(__name__)

# Dev note: Allow all origins so frontend can talk to backend
CORS(app)

# Metrics
REQUESTS = Counter('http_requests_total', 'Total HTTP Requests')
SHORTENED = Counter('shortened_urls_total', 'Total Shortened URLs')

# --- Database Configuration (Connection Pool) ---
DB_HOST = "db"
DB_NAME = os.environ.get('POSTGRES_DB', 'urldb')
DB_USER = os.environ.get('POSTGRES_USER', 'devuser')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'devpassword')

# Global pool variable
db_pool = None

def get_db_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = pool.SimpleConnectionPool(
                1, 20, # Min 1 connection, Max 20
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
        except Exception as e:
            print(f"[CRITICAL] Failed to create DB pool: {e}")
    return db_pool

def get_conn():
    p = get_db_pool()
    return p.getconn() if p else None

def release_conn(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

def init_db():
    """Automatically creates the table on startup"""
    conn = get_conn()
    if not conn:
        print("[INFO] Waiting for Database...")
        return

    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                id SERIAL PRIMARY KEY,
                short_code VARCHAR(10) UNIQUE NOT NULL,
                long_url TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        print("[SUCCESS] Database initialized & table checked.")
    except Exception as e:
        print(f"[ERROR] DB Init failed: {e}")
    finally:
        release_conn(conn)

def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

# --- Routes ---

@app.route('/shorten', methods=['POST'])
def shorten():
    REQUESTS.inc()
    data = request.get_json()
    
    # Note: Frontend sends 'long_url', so we keep using that
    long_url = data.get('long_url')

    if not long_url:
        return jsonify({"error": "Missing long_url"}), 400

    conn = get_conn()
    if not conn:
        return jsonify({"error": "Database unavailable"}), 503

    try:
        # Retry logic: Try 3 times in case of code collision
        for _ in range(3):
            try:
                code = generate_code()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO urls (short_code, long_url) VALUES (%s, %s)",
                    (code, long_url)
                )
                conn.commit()
                cur.close()
                
                SHORTENED.inc()
                return jsonify({"short_code": code}), 201

            except psycopg2.IntegrityError:
                # Collision happened, rollback and try again
                conn.rollback()
                continue
            except Exception as e:
                conn.rollback()
                raise e
        
        return jsonify({"error": "Failed to generate unique code, try again"}), 500

    except Exception as e:
        print(f"[ERROR] Insert failed: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        release_conn(conn)

@app.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    REQUESTS.inc()
    conn = get_conn()
    
    if not conn:
        return abort(503)

    try:
        cur = conn.cursor()
        cur.execute("SELECT long_url FROM urls WHERE short_code = %s", (short_code,))
        record = cur.fetchone()
        cur.close()

        if record:
            return redirect(record[0], code=302)
        return jsonify({"error": "Link not found"}), 404

    except Exception as e:
        print(f"[ERROR] Lookup failed: {e}")
        return jsonify({"error": "Server Error"}), 500
    finally:
        release_conn(conn)

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "db_pool": "active" if db_pool else "down"}), 200

if __name__ == '__main__':
    # Initialize DB table automatically when app starts
    init_db()
    app.run(host='0.0.0.0', port=5000)