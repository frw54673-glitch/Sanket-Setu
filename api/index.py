"""Vercel Serverless Entrypoint for Sanket Setu."""
import os
import sys
import traceback
from pathlib import Path

# Ensure root directory is set for config paths and sys.path
root_dir = Path(__file__).resolve().parent.parent
os.environ["SANKET_SETU_ROOT"] = str(root_dir)

src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

try:
    from sanket_setu.live_server import app
except Exception as exc:
    import logging
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    tb = traceback.format_exc()
    sys.stderr.write(f"CRITICAL_STARTUP_ERROR: {tb}\n")

    app = FastAPI(title="Sanket Setu Diagnostics")

    @app.api_route("/{catchall:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    def error_view(catchall: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "status": "startup_failed",
                "error": str(exc),
                "traceback": tb.splitlines(),
                "root_dir": str(root_dir),
                "cwd": str(Path.cwd()),
                "sys_path": sys.path[:5],
                "files_in_root": [p.name for p in root_dir.iterdir()] if root_dir.exists() else [],
            },
        )
