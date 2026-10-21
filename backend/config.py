"""Local configuration only; never expose credential values through the API."""
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent


def load_backend_env(path: Path | None = None) -> None:
    load_dotenv(path if path is not None else BASE_DIR / '.env', override=False)
