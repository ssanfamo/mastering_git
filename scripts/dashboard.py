# dashboard.py
from flask import Flask, render_template, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)

# Connect to the database created by your monitor
DB_PATH = Path('system_metrics.db')

def get_latest_metrics():
    """Fetch the most recent system metrics from the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, cpu_percent, memory_percent, memory_available_gb, 
                   disk_usage_percent, service_status
            FROM system_metrics 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "timestamp": row[0],
                "cpu_percent": row[1],
                "memory_percent": row[2],
                "memory_available_gb": row[3],
                "disk_usage_percent": row[4],
                "services": json.loads(row[5]) if row[5] else {}
            }
        return {}
    except Exception as e:
        print(f"Database error: {e}")
        return {}

@app.route('/')
def index():
    """Render the main dashboard page."""
    metrics = get_latest_metrics()
    return render_template('dashboard.html', metrics=metrics)

@app.route('/api/metrics')
def api_metrics():
    """JSON API endpoint for latest metrics (for auto-refresh)."""
    metrics = get_latest_metrics()
    return jsonify(metrics)

@app.route('/api/history/<hours>')
def api_history(hours):
    """API endpoint for historical data."""
    try:
        hours_int = int(hours)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cutoff = (datetime.now() - timedelta(hours=hours_int)).isoformat()
        
        cursor.execute('''
            SELECT timestamp, cpu_percent, memory_percent, disk_usage_percent
            FROM system_metrics 
            WHERE timestamp > ?
            ORDER BY timestamp
        ''', (cutoff,))
        
        data = [{
            "time": row[0],
            "cpu": row[1],
            "memory": row[2],
            "disk": row[3]
        } for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)