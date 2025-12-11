# url-shortener/backend/app.py

import os
import random
import string
from flask import Flask, request, redirect, jsonify, abort
from prometheus_flask_exporter import PrometheusMetrics 
import psycopg2
from psycopg2 import extras # For dictionary cursor

app = Flask(__name__)
# Initialize Prometheus metrics on the app
metrics = PrometheusMetrics(app)

# Configuration for Database connection
DB_HOST = os.environ.get('POSTGRES_HOST', 'db')
DB_NAME = os.environ.get('POSTGRES_DB', 'urldb')
DB_USER = os.environ.get('POSTGRES_USER', 'devuser')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'devpassword')
SHORT_CODE_LENGTH = 6

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        # In a real app, you'd handle this more gracefully (e.g., retry)
        return None

def initialize_db():
    """Creates the 'urls' table if it doesn't exist."""
    conn = get_db_connection()
    if conn:
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
        except Exception as e:
            print(f"Error initializing database: {e}")
        finally:
            conn.close()

def generate_short_code(length=SHORT_CODE_LENGTH):
    """Generates a random short code using letters and numbers."""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# --- Application Endpoints ---

@app.before_request
def before_request():
    """Initialize the database before the first request."""
    if not hasattr(app, 'db_initialized'):
        initialize_db()
        app.db_initialized = True

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """Receives a long URL, generates a short code, and saves it."""
    data = request.json
    long_url = data.get('url')

    if not long_url:
        return jsonify({"error": "Missing 'url' in request body."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database service unavailable."}), 503

    try:
        # Generate a unique code (simple retry logic for collision)
        short_code = generate_short_code()
        
        cur = conn.cursor()
        # Insert the new URL mapping
        cur.execute(
            "INSERT INTO urls (short_code, long_url) VALUES (%s, %s)",
            (short_code, long_url)
        )
        conn.commit()
        cur.close()
        
        # Increment a custom Prometheus counter for URLs shortened
        metrics.info('urls_shortened', 'Total number of URLs shortened')
        
        # Return the generated short code
        return jsonify({"short_code": short_code}), 201

    except psycopg2.Error as e:
        conn.rollback()
        print(f"Database error during insert: {e}")
        return jsonify({"error": "Internal database error."}), 500
    finally:
        conn.close()


@app.route('/<short_code>', methods=['GET'])
def redirect_url(short_code):
    """Retrieves the long URL for a given short code and redirects the user."""
    conn = get_db_connection()
    if not conn:
        return abort(503) # Service Unavailable

    try:
        # Use a dict cursor for easier access to column names
        cur = conn.cursor(cursor_factory=extras.DictCursor)
        cur.execute(
            "SELECT long_url FROM urls WHERE short_code = %s",
            (short_code,)
        )
        record = cur.fetchone()
        cur.close()

        if record:
            long_url = record['long_url']
            # Perform the HTTP redirect
            return redirect(long_url, code=302)
        else:
            # If short code not found
            return jsonify({"error": f"Short code '{short_code}' not found."}), 404

    except psycopg2.Error as e:
        print(f"Database error during lookup: {e}")
        return abort(500)
    finally:
        conn.close()

# The /metrics endpoint is automatically added by PrometheusMetrics

if __name__ == '__main__':
    # Initialize DB (only needed when running locally without Gunicorn startup)
    initialize_db() 
    app.run(host='0.0.0.0', port=5000)