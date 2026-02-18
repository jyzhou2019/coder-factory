#!/usr/bin/env python
"""
Run script for Coder-Factory Web Interface

Usage:
    python run_web.py [--host HOST] [--port PORT] [--reload]
"""

import argparse
import uvicorn
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    parser = argparse.ArgumentParser(description="Run Coder-Factory Web Interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    os.makedirs("workspace", exist_ok=True)

    print(f"Starting Coder-Factory Web Interface on {args.host}:{args.port}")
    print(f"Open http://localhost:{args.port} in your browser")
    print("API Documentation: http://localhost:{args.port}/docs")

    uvicorn.run(
        "coder_factory.web.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
