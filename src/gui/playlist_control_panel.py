from pathlib import Path
from typing import Callable, Optional

import customtkinter as ctk

from src.audio import MusicPlayerManager


class PlaylistControlPanel(ctk.CTkFrame):
    def __init__(
        self,
        master,
        player_manager: MusicPlayerManager,
        on_change: Optional[Callable[[Optional[Path]], None]] = None,
        **kwargs,
    ) -> None:
        super().__init__(master, **kwargs)
        self.player_manager = player_manager
        self.status_var = ctk.StringVar(value="Playback idle.")
        self.on_change = on_change

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=8, pady=6)
        button_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1, uniform="controls")

        play_btn = ctk.CTkButton(button_frame, text="Play", command=self._play)
        play_btn.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        pause_btn = ctk.CTkButton(button_frame, text="Pause", command=self._pause)
        pause_btn.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        stop_btn = ctk.CTkButton(button_frame, text="Stop", command=self._stop)
        stop_btn.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        prev_btn = ctk.CTkButton(button_frame, text="Previous", command=self._previous)
        prev_btn.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        next_btn = ctk.CTkButton(button_frame, text="Next", command=self._next)
        next_btn.grid(row=0, column=4, padx=6, pady=6, sticky="ew")

        self.shuffle_btn = ctk.CTkButton(
            button_frame,
            text="Shuffle",
            command=self._toggle_shuffle,
            fg_color="#2b2b2b",
            hover_color="#3c3c3c",
        )
        self.shuffle_btn.grid(row=0, column=5, padx=6, pady=6, sticky="ew")

        status_label = ctk.CTkLabel(self, textvariable=self.status_var, text_color="gray", font=("Segoe UI", 11))
        status_label.pack(pady=(2, 8))

    def _play(self) -> None:
        try:
            track = self.player_manager.play()
        except Exception as exc:
            self.status_var.set(f"Cannot play: {exc}")
            return

        if track:
            self.status_var.set(f"Playing {Path(track).stem}")
        else:
            self.status_var.set("No track in playlist.")
        self._notify(track)

    def _stop(self) -> None:
        self.player_manager.stop()
        self.status_var.set("Stopped.")
        self._notify(self.player_manager.get_current_track())

    def _pause(self) -> None:
        self.player_manager.pause()
        self.status_var.set("Paused.")
        self._notify(self.player_manager.get_current_track())

    def _next(self) -> None:
        try:
            track = self.player_manager.next()
        except Exception as exc:
            self.status_var.set(f"Cannot skip: {exc}")
            return

        if track:
            self.status_var.set(f"Playing {Path(track).stem}")
        else:
            self.status_var.set("No next track.")
        self._notify(track)

    def _previous(self) -> None:
        try:
            track = self.player_manager.previous()
        except Exception as exc:
            self.status_var.set(f"Cannot go back: {exc}")
            return

        if track:
            self.status_var.set(f"Playing {Path(track).stem}")
        else:
            self.status_var.set("No previous track.")
        self._notify(track)

    def _toggle_shuffle(self) -> None:
        state = self.player_manager.toggle_shuffle()
        if state:
            self.shuffle_btn.configure(fg_color="#1db954", hover_color="#169b43")
            self.status_var.set("Shuffle: ON")
        else:
            self.shuffle_btn.configure(fg_color="#2b2b2b", hover_color="#3c3c3c")
            self.status_var.set("Shuffle: OFF")
    def _notify(self, track: Optional[Path]) -> None:
        if self.on_change:
            try:
                self.on_change(track)
            except Exception:
                pass
