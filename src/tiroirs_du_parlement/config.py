import os
from pathlib import Path

DATA_PATH = Path("data")
DIST_PATH = Path("dist")
WEB_PATH = Path("web")

META_PATH = DATA_PATH / Path("meta.json")
OUTPUT_PATH = DIST_PATH / Path("output.json")

IS_CI_ENV = os.environ.get("CI", "false").lower() == "true"  # e.g. GitHub Actions
SERVER_PORT = int(os.environ.get("PORT", 8000))
