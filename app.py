# ==============================================================================
# ߖ️ TERI FUSION - PROCESSING SERVER (VERSI STABIL)
# ==============================================================================

import os
import time
import json
import uuid
import threading
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.middleware.proxy_fix import ProxyFix

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ==============================================================================
# ߓ KONFIGURASI
# ==============================================================================

UPLOAD_FOLDER = "/tmp/uploads"
RESULTS_FOLDER = "/tmp/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

JOBS = {}  # job_id -> status

# ==============================================================================
# ߏ ROOT ENDPOINT (Health check)
# ==============================================================================

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'ߚ TERI FUSION Processing Server',
        'version': '1.0',
        'timestamp': datetime.now().isoformat()
    })

# ==============================================================================
# ߔ HEALTH CHECK (Penting untuk Railway)
# ==============================================================================

@app.route('/health')
def health():
    """Endpoint untuk Railway health check"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/ping')
def ping():
    """Endpoint sederhana untuk test koneksi"""
    return 'pong'

# ==============================================================================
# ߓ UPLOAD ENDPOINT
# ==============================================================================

@app.route('/upload', methods=['POST'])
def upload_file():
    """Menerima file CSV dari Panglima"""
    try:
        job_id = str(uuid.uuid4())[:8]
        file = request.files.get('file')
        chat_id = request.form.get('chat_id')
        token = request.form.get('token')
        
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
        
        # Simpan file
        filename = f"{job_id}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Catat job
        JOBS[job_id] = {
            'status': 'pending',
            'filepath': filepath,
            'chat_id': chat_id,
            'token': token,
            'created': time.time()
        }
        
        # Mulai proses di background
        threading.Thread(target=process_job, args=(job_id,), daemon=True).start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'File received, processing started'
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# ߔ STATUS ENDPOINT
# ==============================================================================

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    try:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify({
            'job_id': job_id,
            'status': job['status'],
            'progress': job.get('progress', 0)
        })
    except Exception as e:
        logger.error(f"Status error: {e}")
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# ߓ RESULT ENDPOINT
# ==============================================================================

@app.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    try:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job['status'] != 'completed':
            return jsonify({'error': 'Result not ready'}), 202
        
        return send_file(job['result_file'], as_attachment=True)
        
    except Exception as e:
        logger.error(f"Result error: {e}")
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# ⚙️ PROCESSING (Simulasi dulu)
# ==============================================================================

def process_job(job_id):
    """Proses file di background"""
    try:
        job = JOBS[job_id]
        job['status'] = 'processing'
        job['progress'] = 10
        
        # Simulasi proses panjang
        time.sleep(2)
        job['progress'] = 30
        
        time.sleep(2)
        job['progress'] = 60
        
        time.sleep(2)
        job['progress'] = 90
        
        # Buat hasil dummy
        result = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'dna_recommendation': {
                'stop_loss': 0.35,
                'trailing_start': 0.22,
                'trailing_distance': 0.12,
                'max_spread': 28,
                'min_volume': 75
            }
        }
        
        result_file = os.path.join(RESULTS_FOLDER, f"{job_id}_results.json")
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        job['result_file'] = result_file
        job['status'] = 'completed'
        job['progress'] = 100
        
        logger.info(f"Job {job_id} completed")
        
    except Exception as e:
        logger.error(f"Processing error for job {job_id}: {e}")
        job['status'] = 'failed'
        job['error'] = str(e)

# ==============================================================================
# ߚ MAIN
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"ߚ Server starting on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
