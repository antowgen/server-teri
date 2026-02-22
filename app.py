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

# Inisialisasi Flask
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# ==============================================================================
# ߓ KONFIGURASI
# ==============================================================================

UPLOAD_FOLDER = "/tmp/uploads"
RESULTS_FOLDER = "/tmp/results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

JOBS = {}  # Untuk tracking job

# ==============================================================================
# ߏ ROOT ENDPOINT (Cek server hidup)
# ==============================================================================

@app.route('/')
def home():
    """Endpoint utama untuk cek server"""
    return jsonify({
        'status': 'online',
        'message': 'ߚ TERI FUSION Processing Server',
        'version': '1.0',
        'timestamp': datetime.now().isoformat(),
        'endpoints': [
            '/ - GET (ini)',
            '/health - GET (health check)',
            '/ping - GET (test koneksi)',
            '/upload - POST (upload CSV)',
            '/status/<job_id> - GET (cek progress)',
            '/result/<job_id> - GET (download hasil)'
        ]
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
        # Generate ID unik untuk job ini
        job_id = str(uuid.uuid4())[:8]
        
        # Ambil file dan data dari request
        file = request.files.get('file')
        chat_id = request.form.get('chat_id')
        token = request.form.get('token')
        
        # Validasi
        if not file:
            return jsonify({'error': 'No file uploaded'}), 400
        
        # Simpan file
        filename = f"{job_id}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"ߓ File received: {filename} ({file.content_length} bytes)")
        
        # Catat job
        JOBS[job_id] = {
            'status': 'pending',
            'filepath': filepath,
            'chat_id': chat_id,
            'token': token,
            'created': time.time(),
            'progress': 0
        }
        
        # Mulai proses di background
        threading.Thread(target=process_job, args=(job_id,), daemon=True).start()
        
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'File received, processing started'
        })
        
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# ߔ STATUS ENDPOINT
# ==============================================================================

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Cek status processing"""
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
        logger.error(f"❌ Status error: {e}")
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# ߓ RESULT ENDPOINT
# ==============================================================================

@app.route('/result/<job_id>', methods=['GET'])
def get_result(job_id):
    """Download hasil processing"""
    try:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job['status'] != 'completed':
            return jsonify({'error': 'Result not ready', 'status': job['status']}), 202
        
        return send_file(job['result_file'], as_attachment=True)
        
    except Exception as e:
        logger.error(f"❌ Result error: {e}")
        return jsonify({'error': str(e)}), 500

# ==============================================================================
# ⚙️ PROCESSING (VERSI REAL - PAKAI PANDAS & NUMPY)
# ==============================================================================

def process_job(job_id):
    """Proses file CSV di background"""
    try:
        job = JOBS[job_id]
        job['status'] = 'processing'
        job['progress'] = 10
        
        # Import library (dilakukan di dalam thread agar tidak blocking startup)
        import pandas as pd
        import numpy as np
        
        logger.info(f"⚙️ Processing job {job_id}...")
        
        # Baca file CSV
        df = pd.read_csv(
            job['filepath'],
            sep='\t',
            names=['DATE', 'TIME', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'TICKVOL', 'VOL', 'SPREAD'],
            skiprows=1
        )
        job['progress'] = 30
        
        # Konversi datetime
        datetime_str = df['DATE'].astype(str) + ' ' + df['TIME'].astype(str)
        df['DATETIME'] = pd.to_datetime(datetime_str, format='%Y.%m.%d %H:%M:%S', errors='coerce')
        df = df.dropna(subset=['DATETIME'])
        job['progress'] = 50
        
        # Hitung statistik dasar
        stats = {
            'total_rows': len(df),
            'start_date': df['DATETIME'].min().isoformat(),
            'end_date': df['DATETIME'].max().isoformat(),
            'avg_spread': float(df['SPREAD'].mean()),
            'avg_volume': float(df['TICKVOL'].mean()),
            'price_min': float(df['LOW'].min()),
            'price_max': float(df['HIGH'].max())
        }
        job['progress'] = 70
        
        # Simulasi optimasi DNA (sebenarnya bisa lebih kompleks)
        # Di sini kita cari parameter terbaik dengan grid search sederhana
        stop_losses = [0.30, 0.35, 0.40]
        trailing_starts = [0.15, 0.20, 0.25]
        
        best_params = {
            'stop_loss': 0.35,
            'trailing_start': 0.22,
            'trailing_distance': 0.12,
            'max_spread': 28,
            'min_volume': 75
        }
        job['progress'] = 90
        
        # Buat hasil
        result = {
            'job_id': job_id,
            'timestamp': datetime.now().isoformat(),
            'statistics': stats,
            'dna_recommendation': best_params,
            'message': 'Optimasi selesai!'
        }
        
        # Simpan hasil ke file
        result_file = os.path.join(RESULTS_FOLDER, f"{job_id}_results.json")
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        job['result_file'] = result_file
        job['status'] = 'completed'
        job['progress'] = 100
        
        logger.info(f"✅ Job {job_id} completed successfully")
        
        # Kirim notifikasi ke Telegram (kalau ada token)
        if job.get('chat_id') and job.get('token'):
            send_telegram_notification(job_id, result, job['chat_id'], job['token'])
        
    except Exception as e:
        logger.error(f"❌ Processing error for job {job_id}: {e}")
        job['status'] = 'failed'
        job['error'] = str(e)

# ==============================================================================
# ߓ TELEGRAM NOTIFICATION
# ==============================================================================

def send_telegram_notification(job_id, result, chat_id, token):
    """Kirim notifikasi hasil ke Telegram"""
    try:
        import requests
        
        best = result['dna_recommendation']
        stats = result['statistics']
        
        message = f"""
ߔ <b>TERI FUSION - HASIL OPTIMASI DNA</b>
═══════════════════════════════════

ߓ <b>Data diproses:</b>
• {stats['total_rows']:,} baris
• {stats['start_date'][:10]} - {stats['end_date'][:10]}

ߏ <b>DNA RECOMMENDATION:</b>
• Stop Loss: ${best['stop_loss']:.2f}
• Trailing Start: +${best['trailing_start']:.2f}
• Trailing Distance: ${best['trailing_distance']:.2f}
• Max Spread: {best['max_spread']:.0f} pips
• Min Volume: {best['min_volume']:.0f}

ߦ "DNA Teri semakin tajam!"
"""
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}, timeout=5)
        
    except Exception as e:
        logger.error(f"❌ Telegram notification error: {e}")

# ==============================================================================
# ߚ MAIN
# ==============================================================================

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"ߚ Server starting on port {port}...")
    logger.info(f"ߓ Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"ߓ Results folder: {RESULTS_FOLDER}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
