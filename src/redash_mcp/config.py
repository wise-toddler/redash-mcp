"""Redash MCP configuration."""
import os

URL = os.environ.get("REDASH_URL", "").rstrip("/")
API_KEY = os.environ.get("REDASH_API_KEY", "")
TIMEOUT = int(os.environ.get("REDASH_TIMEOUT", "30"))

if not URL or not API_KEY:
    raise ValueError("REDASH_URL and REDASH_API_KEY environment variables are required")

HEADERS = {
    "Authorization": f"Key {API_KEY}",
    "Content-Type": "application/json"
}
