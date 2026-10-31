"""Root entrypoint for Vercel zero-config FastAPI support."""
import os
import sys
from pathlib import Path

# Ensure root directory is set for config paths and sys.path
root_dir = Path(__file__).resolve().parent
os.environ["SANKET_SETU_ROOT"] = str(root_dir)

src_dir = root_dir / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from api.index import app
