import shutil
import subprocess
from typing import Optional, Tuple


def ffmpeg_available() -> Tuple[bool, Optional[str]]:
    """
    Check if ffmpeg is available on PATH without requiring elevated privileges.
    Returns (is_available, descriptor/first-line).
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return False, None

    try:
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        descriptor = None
        if result.stdout:
            descriptor = result.stdout.splitlines()[0]
        return True, descriptor or ffmpeg_path
    except Exception:
        return True, ffmpeg_path
