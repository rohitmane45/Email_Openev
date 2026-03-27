"""
Email Triage Environment — Server Entry Point
=============================================
Starts the FastAPI server using uvicorn.

Usage:
    python main.py                    # default host=0.0.0.0, port=8000
    python main.py --port 9000        # custom port
    python main.py --host 127.0.0.1   # localhost only
"""

import argparse
import sys

try:
    import uvicorn
except ImportError:
    print("ERROR: uvicorn is not installed. Run: pip install uvicorn")
    sys.exit(1)

try:
    from email_triage_env.server.app import app
except ImportError as e:
    print(f"ERROR: Could not import server app: {e}")
    print("Make sure you installed dependencies: pip install -r requirements.txt")
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email Triage Environment Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    parser.add_argument("--log-level", default="info", help="Log level (default: info)")
    args = parser.parse_args()

    print("=" * 55)
    print("  [EMAIL TRIAGE] Email Triage Environment Server")
    print("  Built for Meta PyTorch OpenEnv Hackathon x Scaler")
    print("=" * 55)
    print(f"  Server     : http://{args.host}:{args.port}")
    print(f"  Docs       : http://{args.host}:{args.port}/docs")
    print(f"  Health     : http://{args.host}:{args.port}/health")
    print(f"  Tools list : http://{args.host}:{args.port}/tools")
    print("=" * 55)
    print("  Press CTRL+C to stop\n")

    uvicorn.run(
        "email_triage_env.server.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )
