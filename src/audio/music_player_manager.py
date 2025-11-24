from __future__ import annotations

from pathlib import Path
from threading import Lock
import random
from typing import List, Optional
from urllib.parse import quote

from src.sonos import SonosDeviceHandle


class MusicPlayerManager:
    """
    Singleton manager to coordinate playback and maintain a simple playlist queue.
    """

    _instance: Optional["MusicPlayerManager"] = None
    _instance_lock = Lock()

    def __init__(self) -> None:
        self.device: Optional[SonosDeviceHandle] = None
        self.device_name: Optional[str] = None
        self._playlist: List[Path] = []
        self._current_index: int = 0
        self._playlist_lock = Lock()
        self.stream_base_url: Optional[str] = None
        self._current_track: Optional[Path] = None
        self._user_stopped: bool = False
        self.shuffle: bool = False

    @classmethod
    def instance(cls) -> "MusicPlayerManager":
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def set_device(self, handle: SonosDeviceHandle) -> None:
        self.device = handle
        self.device_name = handle.player_name
        self._user_stopped = False

    def set_stream_base_url(self, base_url: str) -> None:
        self.stream_base_url = base_url.rstrip("/")

    def add_song(self, path: Path) -> None:
        track = Path(path).resolve()
        if not track.exists():
            raise FileNotFoundError(f"Track not found: {track}")
        with self._playlist_lock:
            self._playlist.append(track)

    def remove_song(self, path: Path) -> bool:
        target = Path(path).resolve()
        with self._playlist_lock:
            for idx, track in enumerate(self._playlist):
                if track.resolve() == target:
                    self._playlist.pop(idx)
                    if idx < self._current_index:
                        self._current_index = max(0, self._current_index - 1)
                    elif idx == self._current_index and self._current_index >= len(self._playlist):
                        self._current_index = max(0, len(self._playlist) - 1)
                    return True
        return False

    def get_playlist(self) -> List[Path]:
        with self._playlist_lock:
            return list(self._playlist)

    def _play_track(self, track: Path) -> None:
        if not self.device:
            print("No Sonos device set for playback.")
            raise RuntimeError("No Sonos device set for playback.")
        if not self.stream_base_url:
            print("No stream server configured for playback.")
            raise RuntimeError("No stream server configured for playback.")

        print("Playing track:", track)

        uri = self._build_track_uri(track)
        print(uri)
        self.device.sonos.play_uri(uri)

    def _build_track_uri(self, track: Path) -> str:
        filename = quote(track.name)
        return f"{self.stream_base_url}/{filename}"

    def play(self) -> Optional[Path]:
        with self._playlist_lock:
            if not self._playlist:
                return None
            if self._current_index >= len(self._playlist):
                self._current_index = 0
            track = self._playlist[self._current_index]
        print("TRACK: ", track)
        self._play_track(track)
        self._current_track = track
        self._user_stopped = False
        return track

    def play_track(self, path: Path) -> Path:
        target = Path(path).resolve()
        with self._playlist_lock:
            for idx, track in enumerate(self._playlist):
                if track.resolve() == target:
                    self._current_index = idx
                    break
            else:
                raise ValueError("Track not found in playlist.")
            track = self._playlist[self._current_index]
        self._play_track(track)
        self._current_track = track
        self._user_stopped = False
        return track

    def stop(self) -> None:
        if self.device:
            self.device.sonos.stop()
        self._user_stopped = True
        self._current_track = None

    def pause(self) -> None:
        if self.device:
            self.device.sonos.pause()
        self._current_track = self.get_current_track()
        self._user_stopped = False

    def next(self) -> Optional[Path]:
        with self._playlist_lock:
            if not self._playlist:
                return None
            if self.shuffle:
                self._current_index = random.randrange(len(self._playlist))
            else:
                self._current_index = (self._current_index + 1) % len(self._playlist)
            track = self._playlist[self._current_index]
        self._play_track(track)
        self._current_track = track
        self._user_stopped = False
        return track

    def previous(self) -> Optional[Path]:
        with self._playlist_lock:
            if not self._playlist:
                return None
            if self.shuffle:
                self._current_index = random.randrange(len(self._playlist))
            else:
                self._current_index = (self._current_index - 1) % len(self._playlist)
            track = self._playlist[self._current_index]
        self._play_track(track)
        self._current_track = track
        self._user_stopped = False
        return track

    def get_current_track(self) -> Optional[Path]:
        with self._playlist_lock:
            if not self._playlist:
                return None
            if self._current_index >= len(self._playlist):
                self._current_index = max(0, len(self._playlist) - 1)
            return self._playlist[self._current_index] if self._playlist else None

    def get_transport_state(self) -> Optional[str]:
        if not self.device:
            return None
        try:
            info = self.device.sonos.get_current_transport_info()
            return info.get("current_transport_state")
        except Exception:
            return None

    def poll_and_maybe_advance(self) -> None:
        """
        Poll current transport state and auto-advance when playback stops naturally.
        """
        state = self.get_transport_state()
        if not state:
            return

        if state == "STOPPED" and not self._user_stopped and self._current_track:
            if self._playlist:
                self.next()

    def toggle_shuffle(self) -> bool:
        self.shuffle = not self.shuffle
        return self.shuffle

    # Volume passthrough
    def get_volume(self) -> Optional[int]:
        if not self.device:
            return None
        return self.device.get_volume()

    def set_volume(self, volume: int) -> Optional[int]:
        if not self.device:
            return None
        return self.device.set_volume(volume)

    def change_volume(self, delta: int) -> Optional[int]:
        if not self.device:
            return None
        return self.device.change_volume(delta)
