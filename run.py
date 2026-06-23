#!/usr/bin/env python
"""
Virtual Tailor API Launcher
Usage: python run.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app import create_app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)