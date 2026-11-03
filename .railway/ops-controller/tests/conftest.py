"""Test setup: Config reads the environment at import time, so set it first."""
import os
import sys
from pathlib import Path

os.environ.update({
    "DIGITALOCEAN_TOKEN": "x",
    "RAILWAY_API_TOKEN": "x",
    "RAILWAY_PROJECT_ID": "p",
    "RAILWAY_ENVIRONMENT_ID": "e1234567",
    "RAILWAY_SERVICE_ID": "svc-ops",
    "DATABASE_URL": "postgresql://x",
    "TRIGGER_VERSION": "v4.8.3",
    "TRIGGER_WORKER_TOKEN": "",
})

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
