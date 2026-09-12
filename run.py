#!/usr/bin/env python
"""
UberOKX - Plateforme Trading AI
Entry point for running the FastAPI application.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the FastAPI app
from backend.main import app


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  ÜBEROKX - Plateforme Trading AI")
    print("  Mode: PAPER (simulé)")
    print("  Accès: http://127.0.0.1:8080")
    print("=" * 60)

    # Run with Uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8080,
        log_level="info",
    )
