#!/usr/bin/env python3
"""
DOI Management System - Main application entry point
"""

import os
from app import create_app

# Create Flask application instance
app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    # This allows running the app with: python app.py
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "True").lower() == "true",
    )
