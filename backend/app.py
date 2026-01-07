import os
import time
import random
import string
import psycopg2
from psycopg2 import pool
from flask import Flask, request, jsonify, redirect, abort
from flask_cors import CORS
from prometheus_client import Counter, generate_latest
import re

app = Flask(__name__)
CORS(app)

# Metrics
REQUESTS = Counter('http_requests_total', 'Total HTTP Requests')
SHORTENED = Counter('shortened_urls_total', 'Total Shortened URLs')

# Database Configuration
DB_HOST = os.environ.get('POSTGRES_HOST', 'database-service')
DB_NAME = os.environ.get('POSTGRES_DB', 'hostdb')
DB_USER = os.environ.get('POSTGRES_USER', 'devuser')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'devpassword')

db_pool = None

def is_valid_url(url):
    # This regex is now on its own separate lines to prevent syntax errors
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
    return p.getconn() if p else None

def release_conn(conn):
    if db_pool and conn:
        db_pool.putconn(conn)

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
    REQUESTS.inc()
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON provided"}), 400
        
    long_url = data.get('long_url', '').strip()

    if not long_url:
        return jsonify({"error": "Missing long_url"}), 400

    if not is_valid_url(long_url):
        return jsonify({"error": "Invalid URL format"}), 400

    if not long_url.startswith(('http://', 'https://')):
        long_url = 'https://' + long_url

    conn = get_conn()
    if not conn: return jsonify({"error": "Database unavailable"}), 503

    try:
        cur = conn.cursor()
        for _ in range(3):
            try:
                code = generate_code()
                cur.execute("INSERT INTO urls (short_code, long_url) VALUES (%s, %s)", (code, long_url))
                conn.commit()
                SHORTENED.inc()
                cur.close()
                return jsonify({"short_code": code}), 201
            except psycopg2.IntegrityError:
                conn.rollback()
                continue
        cur.close()
        return jsonify({"error": "Collision"}), 500
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": "Internal error"}), 500
    finally:
        release_conn(conn)

@app.route('/r/<short_code>', methods=['GET'])
def redirect_url(short_code):
    REQUESTS.inc()
    conn = get_conn()
    if not conn: return abort(503)
    try:
        cur = conn.cursor()
        cur.execute("SELECT long_url FROM urls WHERE short_code = %s", (short_code,))
        record = cur.fetchone()
        cur.close()
        if record:
            return redirect(record[0], code=302)
        return jsonify({"error": "Not found"}), 404
    finally:
        release_conn(conn)

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# Perform the table check outside the main loop
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)