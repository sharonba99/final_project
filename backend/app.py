import os
import time
import random
import string
import re
from flask import Flask, redirect, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Api, Resource, reqparse
from prometheus_client import Counter, Histogram, Gauge, generate_latest

app = Flask(__name__)
CORS(app)  # Enables Cross-Origin Resource Sharing

# --- Database Configuration ---
DB_USER = os.environ.get('POSTGRES_USER', 'devuser')
DB_PASS = os.environ.get('POSTGRES_PASSWORD', 'devpassword')
DB_HOST = os.environ.get('POSTGRES_HOST', 'database-headless-service')
DB_NAME = os.environ.get('POSTGRES_DB', 'hostdb')

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
api = Api(app)

# --- Prometheus Metrics ---
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'Request duration', ['endpoint'])
IN_PROGRESS = Gauge('http_requests_in_progress', 'Requests currently in progress')
DB_CONNECTIONS = Gauge('db_connections_active', 'Active DB connections')

# --- Database Model ---
class URL(db.Model):
    __tablename__ = 'urls'
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    long_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# --- Helpers ---
def generate_code(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))

def is_valid_url(url):
    pattern = re.compile(r'^(https?://)?([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}(:[0-9]+)?(/.*)?$', re.IGNORECASE)
    return bool(pattern.match(url))

# --- Middleware ---
@app.before_request
def before_request():
    request.start_time = time.time()
    IN_PROGRESS.inc()

@app.after_request
def after_request(response):
    request_latency = time.time() - request.start_time
    IN_PROGRESS.dec()
    REQUEST_COUNT.labels(request.method, request.endpoint).inc()
    REQUEST_LATENCY.labels(request.endpoint).observe(request_latency)
    return response

# --- API Resources ---
class ShortenAPI(Resource):
    def post(self):
        """ Creates a new short link (Create) """
        parser = reqparse.RequestParser()
        parser.add_argument('long_url', required=True, help="long_url cannot be blank")
        args = parser.parse_args()
        
        long_url = args['long_url'].strip()

        if not is_valid_url(long_url):
            return {'error': 'Invalid URL format'}, 400

        if not long_url.startswith(('http://', 'https://')):
            long_url = 'https://' + long_url

        code = generate_code()
        retries = 0
        while URL.query.filter_by(short_code=code).first():
            if retries > 5: return {'error': 'Server busy'}, 500
            code = generate_code()
            retries += 1

        try:
            new_link = URL(short_code=code, long_url=long_url)
            db.session.add(new_link)
            db.session.commit()
            return {'short_code': code}, 201
        except Exception as e:
            db.session.rollback()
            return {'error': 'Database error'}, 500

class URLAdminAPI(Resource):
    def delete(self, short_code):
        """ Deletes a link (Delete - Critical for CRUD requirement) """
        link = URL.query.filter_by(short_code=short_code).first()
        if not link:
            return {'error': 'Not found'}, 404
        
        try:
            db.session.delete(link)
            db.session.commit()
            return {'message': 'Deleted successfully'}, 200
        except:
            db.session.rollback()
            return {'error': 'Delete failed'}, 500

api.add_resource(ShortenAPI, '/shorten')
api.add_resource(URLAdminAPI, '/api/urls/<short_code>')

# --- Routes ---
@app.route('/<short_code>', methods=['GET'])
def redirect_to_url(short_code):
    link = URL.query.filter_by(short_code=short_code).first()
    if link:
        return redirect(link.long_url)
    return jsonify({'error': 'Link not found'}), 404

# --- Health & Metrics ---
@app.route('/metrics')
def metrics():
    try:
        DB_CONNECTIONS.set(1) 
    except:
        DB_CONNECTIONS.set(0)
    return generate_latest(), 200, {'Content-Type': 'text/plain'}

@app.route('/health')
def health_basic():
    return jsonify({"status": "healthy"}), 200

@app.route('/health/live')
def health_liveness():
    return jsonify({"status": "alive"}), 200

@app.route('/health/ready')
def health_readiness():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({"status": "ready", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "error": str(e)}), 503

# --- Initialization ---
def init_db_with_retry():
    with app.app_context():
        for i in range(10):
            try:
                db.create_all()
                print(f"[INFO] DB initialized successfully on attempt {i+1}.")
                return
            except Exception as e:
                time.sleep(2)
        print("[CRITICAL] DB Init failed.")

init_db_with_retry()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)