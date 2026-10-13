# -*- coding: utf-8 -*-
"""Uvicorn ASGI entry point.

Run the development server with:

    python main.py

Or directly with uvicorn:

    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
"""

import sys
import webbrowser
import uvicorn

# Fix Windows console encoding
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.main import app  # noqa: F401

PORT = 8000
HOST = "127.0.0.1"

if __name__ == "__main__":
    print("\nSkill Gap Analyzer starting...")
    print(f"    Web App     -->  http://localhost:{PORT}")
    print(f"    Swagger UI  -->  http://localhost:{PORT}/docs")
    print(f"    Stop server -->  Ctrl+C\n")

    webbrowser.open(f"http://localhost:{PORT}")

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=True,
        log_level="info",
    )
