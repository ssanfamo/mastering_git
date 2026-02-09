from flask import Flask, render_template
import socket
import sys

print("=" * 60)
print("MINIMAL FLASK TEST")
print("=" * 60)
print(f"Python: {sys.version}")
print(f"Hostname: {socket.gethostname()}")

app = Flask(__name__)

@app.route('/')
def home():
    return '<h1 style="color: green;">🎉 FLASK IS WORKING!</h1>' + \
           '<p>If you see this, the server is running.</p>' + \
           '<p><a href="/template">Test template rendering</a></p>'

@app.route('/template')
def template_test():
    try:
        return render_template('dashboard.html')
    except Exception as e:
        return f'<h1 style="color: red;">Template Error: {e}</h1>'

if __name__ == '__main__':
    print("\nStarting server on MULTIPLE PORTS...")
    print("Try these URLs in your browser:")
    print("1. http://localhost:5001 (recommended)")
    print("2. http://127.0.0.1:5001")
    print("3. Your IP address (check console output)")
    print("\nPress Ctrl+C to stop")
    print("=" * 60)
    
    # Try multiple ports
    import threading
    
    def run_on_port(port):
        from waitress import serve
        print(f"\nStarting Waitress on port {port}...")
        serve(app, host='0.0.0.0', port=port)
    
    # Start main development server
    app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
