from __future__ import annotations

from collections import deque
from pathlib import Path
from threading import Lock, Thread
from typing import Callable, Deque, Optional, Tuple
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

from src.misc.pathing import DOWNLOADS_DIR, ensure_downloads_dir


def is_valid_url(candidate: str) -> bool:
    parsed = urlparse(candidate)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def download_audio(url: str) -> Path:
    """
    Download audio as WAV into the downloads directory using yt-dlp's
    equivalent of `-x --audio-format=wav`.
    """
    ensure_downloads_dir()
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "0",
            }
        ],
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # yt-dlp writes a WAV via FFmpegExtractAudio; prefer explicit path.
        if info.get("requested_downloads"):
            output_path = Path(info["requested_downloads"][0]["filepath"])
        else:
            output_path = DOWNLOADS_DIR / f"{info.get('title', 'output')}.wav"
    return output_path.resolve()


class AudioDownloadManager:
    """
    Singleton manager that queues URLs and processes them one at a time.
    """

    _instance: Optional["AudioDownloadManager"] = None
    _instance_lock = Lock()

    def __init__(self) -> None:
        self._queue: Deque[Tuple[str, Optional[Callable[[str, Optional[Path], Optional[Exception]], None]]]] = deque()
        self._queue_lock = Lock()
        self._downloading = False
        self._worker: Optional[Thread] = None
        ensure_downloads_dir()

    @classmethod
    def instance(cls) -> "AudioDownloadManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def enqueue(
        self,
        url: str,
        on_complete: Optional[Callable[[str, Optional[Path], Optional[Exception]], None]] = None,
    ) -> None:
        """
        Add a URL to the queue and kick off a download worker if idle.
        """
        with self._queue_lock:
            self._queue.append((url, on_complete))
            should_start = not self._downloading
            if should_start:
                self._downloading = True

        if should_start:
            self._start_worker()

    def _start_worker(self) -> None:
        self._worker = Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _worker_loop(self) -> None:
        while True:
            with self._queue_lock:
                if not self._queue:
                    self._downloading = False
                    break
                url, callback = self._queue.popleft()

            error: Optional[Exception] = None
            result_path: Optional[Path] = None
            try:
                result_path = download_audio(url)
            except Exception as exc:
                error = exc

            # Invoke callback outside the lock to avoid deadlocks.
            if callback:
                try:
                    callback(url, result_path, error)
                except Exception:
                    # Swallow callback errors to keep worker alive.
                    pass
