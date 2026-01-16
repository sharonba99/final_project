import os
import time
import random
import string
import psycopg2
from psycopg2 import pool
from flask import Flask, request, jsonify, redirect, abort
from flask_cors import CORS
from prometheus_client import Counter, generate_latest, Histogram, Gauge # Added Histogram and Gauge
import re

app = Flask(__name__)
CORS(app)

# --- Prometheus Metrics ---
# 1. Total Requests (Counter) - Added labels for better filtering
REQUESTS = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'http_status'])

# 2. Request Duration (Histogram)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds', 
    'Time spent processing request', 
    ['endpoint'],
    buckets=(.05, .1, .25, .5, 1, 2.5, 5, 10)
)

# 3. Requests in Progress (Gauge)
IN_PROGRESS = Gauge('http_requests_in_progress', 'Total requests currently being processed')

# 4. Active DB Connections (Gauge)
DB_CONNECTIONS = Gauge('db_connections_active', 'Current active database connections')

# 5. Total Shortened URLs (Counter)
SHORTENED = Counter('shortened_urls_total', 'Total Shortened URLs')

# --- Metrics Management Hooks ---
# This ensures IN_PROGRESS is always balanced and never goes below zero
@app.before_request
def start_request_tracking():
    if not request.path.startswith('/health') and request.path != '/metrics':
        IN_PROGRESS.inc()

@app.teardown_request
def stop_request_tracking(exception=None):
    if not request.path.startswith('/health') and request.path != '/metrics':
        IN_PROGRESS.dec()

# Database Configuration
DB_HOST = os.environ.get('POSTGRES_HOST', 'database-service')
DB_NAME = os.environ.get('POSTGRES_DB', 'hostdb')
DB_USER = os.environ.get('POSTGRES_USER', 'devuser')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'devpassword')

db_pool = None

def is_valid_url(url):
    url_pattern = re.compile(
        r'^(https?://)?' 
        r'([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}' 
        r'(:[0-9]+)?'
        r'(/.*)?$', re.IGNORECASE
    )
    return re.match(url_pattern, url) is not None

def get_db_pool():
    global db_pool
    if db_pool is None:
        try:
            db_pool = pool.SimpleConnectionPool(
                1, 20,
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
            print("[INFO] Connection pool created")
        except Exception as e:
            print(f"[CRITICAL] Pool creation failed: {e}")
    return db_pool

def get_conn():
    p = get_db_pool()
    if p:
        conn = p.getconn()
        DB_CONNECTIONS.set(len(p._used)) 
        return conn
    return None

def release_conn(conn):
    try:
        if db_pool and conn:
            db_pool.putconn(conn)
    finally:
        if db_pool:
            DB_CONNECTIONS.set(len(db_pool._used))

def init_db():
    print(f"[DEBUG] Attempting to init DB at {DB_HOST}...")
    for i in range(15):
        conn = None
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                connect_timeout=5
            )
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
            conn.close()
            print("[SUCCESS] Database initialized.")
            return 
        except Exception as e:
            print(f"[INFO] Connection attempt {i+1} failed: {e}")
            if conn: conn.close()
            time.sleep(5)

def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

@app.route('/shorten', methods=['POST', 'OPTIONS'])
def shorten():
    if request.method == 'OPTIONS':
        return '', 204
    
    with REQUEST_DURATION.labels(endpoint='/shorten').time():
        data = request.get_json()
        if not data:
            REQUESTS.labels(method='POST', endpoint='/shorten', http_status=400).inc()
            return jsonify({"error": "No JSON provided"}), 400
            
        long_url = data.get('long_url', '').strip()

        if not long_url:
            REQUESTS.labels(method='POST', endpoint='/shorten', http_status=400).inc()
            return jsonify({"error": "Missing long_url"}), 400

        if not is_valid_url(long_url):
            REQUESTS.labels(method='POST', endpoint='/shorten', http_status=400).inc()
            return jsonify({"error": "Invalid URL format"}), 400

        if not long_url.startswith(('http://', 'https://')):
            long_url = 'https://' + long_url

        conn = get_conn()
        if not conn: 
            REQUESTS.labels(method='POST', endpoint='/shorten', http_status=503).inc()
            return jsonify({"error": "Database unavailable"}), 503

        try:
            cur = conn.cursor()
            for _ in range(3):
                try:
                    code = generate_code()
                    cur.execute("INSERT INTO urls (short_code, long_url) VALUES (%s, %s)", (code, long_url))
                    conn.commit()
                    SHORTENED.inc()
                    REQUESTS.labels(method='POST', endpoint='/shorten', http_status=201).inc()
                    cur.close()
                    return jsonify({"short_code": code}), 201
                except psycopg2.IntegrityError:
                    conn.rollback()
                    continue
            cur.close()
            REQUESTS.labels(method='POST', endpoint='/shorten', http_status=500).inc()
            return jsonify({"error": "Collision"}), 500
        except Exception as e:
            REQUESTS.labels(method='POST', endpoint='/shorten', http_status=500).inc()
            print(f"[ERROR] {e}")
            return jsonify({"error": "Internal error"}), 500
        finally:
            release_conn(conn)

@app.route('/r/<short_code>', methods=['GET'])
def redirect_url(short_code):
    with REQUEST_DURATION.labels(endpoint='/redirect').time():
        conn = get_conn()
        if not conn: 
            REQUESTS.labels(method='GET', endpoint='/redirect', http_status=503).inc()
            return abort(503)
        try:
            cur = conn.cursor()
            cur.execute("SELECT long_url FROM urls WHERE short_code = %s", (short_code,))
            record = cur.fetchone()
            cur.close()
            if record:
                REQUESTS.labels(method='GET', endpoint='/redirect', http_status=302).inc()
                return redirect(record[0], code=302)
            
            REQUESTS.labels(method='GET', endpoint='/redirect', http_status=404).inc()
            return jsonify({"error": "Not found"}), 404
        finally:
            release_conn(conn)

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

@app.route('/health', methods=['GET'])
def health_basic():
    return jsonify({"status": "up", "timestamp": time.time()}), 200

@app.route('/health/live', methods=['GET'])
def health_live():
    return jsonify({"status": "live"}), 200

@app.route('/health/ready', methods=['GET'])
def health_ready():
    """Readiness check - using a direct connection to bypass pool issues."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            connect_timeout=2
        )
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        return jsonify({"status": "ready", "database": "connected"}), 200
    except Exception as e:
        print(f"[HEALTH CHECK FAIL] {e}")
        return jsonify({"status": "not ready", "reason": str(e)}), 503
    finally:
        if conn:
            conn.close()

init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)