from pathlib import Path

# Project root directory (three levels up from this file)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DOWNLOADS_DIR = ROOT_DIR / "downloads"


def ensure_downloads_dir() -> Path:
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    return DOWNLOADS_DIR
