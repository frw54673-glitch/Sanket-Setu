"""Vercel Serverless Entrypoint for Sanket Setu."""
import os
import sys
from pathlib import Path

# Ensure src/ is on sys.path
root_dir = Path(__file__).resolve().parent.parent
src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from sanket_setu.live_server import app

