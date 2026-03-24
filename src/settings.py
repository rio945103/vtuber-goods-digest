import json
from pathlib import Path

from dotenv import load_dotenv
import os


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
MEMBERS_PATH = BASE_DIR / "config" / "members.json"


def load_env_settings() -> dict:
    load_dotenv(ENV_PATH)

    return {
        "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL", ""),
        "DATABASE_PATH": os.getenv("DATABASE_PATH", "data/app.db"),
        "LOG_PATH": os.getenv("LOG_PATH", "logs/app.log"),
    }


def load_members() -> list[dict]:
    with open(MEMBERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["members"]