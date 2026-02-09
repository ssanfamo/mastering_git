# debug_paths.py
import os
from pathlib import Path

print("=" * 60)
print("DEBUG: Checking Flask Template Paths")
print("=" * 60)

# Current directory
current_dir = Path.cwd()
print(f"Current directory: {current_dir}")

# Check for templates folder
templates_path = current_dir / "templates"
print(f"Templates path: {templates_path}")
print(f"Templates exists: {templates_path.exists()}")
print(f"Templates is directory: {templates_path.is_dir()}")

# Check for dashboard.html
dashboard_path = templates_path / "dashboard.html"
print(f"Dashboard.html path: {dashboard_path}")
print(f"Dashboard.html exists: {dashboard_path.exists()}")

# List files in templates if it exists
if templates_path.exists():
    print(f"\nFiles in templates folder:")
    for file in templates_path.iterdir():
        print(f"  - {file.name}")

# Check Flask template loading
try:
    from flask import Flask
    app = Flask(__name__)
    print(f"\nFlask template folder: {app.template_folder}")
    print(f"Flask root path: {app.root_path}")
    
    # Try to find template
    import jinja2
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader([str(templates_path), str(current_dir)])
    )
    print(f"Jinja2 can find dashboard.html: {'dashboard.html' in env.list_templates()}")
    
except Exception as e:
    print(f"\nError testing Flask: {e}")

print("\n" + "=" * 60)
print("QUICK FIXES TO TRY:")
print("1. Make sure 'templates' folder exists in same directory as dashboard.py")
print("2. Make sure 'dashboard.html' is inside 'templates' folder")
print("3. The folder name must be 'templates' (plural, lowercase)")
print("=" * 60)