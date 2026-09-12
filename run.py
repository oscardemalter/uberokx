#!/usr/bin/env python
import sys
import os

# Ajouter le répertoire courant au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Maintenant on peut importer backend
from backend.main_flask import app

if __name__ == "__main__":
    print("=" * 60)
    print("  ÜBEROKX - Plateforme Trading AI")
    print("  Mode: PAPER (simulé)")
    print("  Accès: http://127.0.0.1:8080")
    print("=" * 60)
    app.run(host="127.0.0.1", port=8080, debug=False, threaded=True)
