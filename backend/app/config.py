"""Backend configuration, loaded once when the process starts."""
import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "")


def geoapify_key_status() -> str:
    return "key is configured" if GEOAPIFY_API_KEY.strip() else "key is not configured"
