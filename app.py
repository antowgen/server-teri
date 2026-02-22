import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "online", "message": "TERI FUSION Server Siap!"})

@app.route('/upload', methods=['POST'])
def upload():
    return jsonify({"job_id": "test123", "status": "pending"})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
