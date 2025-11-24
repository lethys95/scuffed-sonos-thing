from pathlib import Path

import customtkinter as ctk

from src.audio import MusicPlayerManager
from src.gui.downloads_list import list_wav_files


class PlaylistManagerFrame(ctk.CTkFrame):
    def __init__(self, master, downloads_dir: Path, player_manager: MusicPlayerManager, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.downloads_dir = downloads_dir
        self.player_manager = player_manager

        self.selection_var = ctk.StringVar()
        self.status_var = ctk.StringVar(value="Add WAVs from downloads to the playlist queue.")

        header = ctk.CTkLabel(self, text="Playlist", font=("Segoe UI", 14))
        header.pack(pady=(4, 2))

        add_frame = ctk.CTkFrame(self)
        add_frame.pack(fill="x", padx=8, pady=(4, 8))

        self.selector = ctk.CTkOptionMenu(add_frame, variable=self.selection_var, values=[], fg_color=None, button_color=None)
        self.selector.pack(side="left", expand=True, fill="x", padx=(12, 8), pady=8)

        self.add_button = ctk.CTkButton(add_frame, text="Add to Playlist", command=self._handle_add, width=130)
        self.add_button.pack(side="right", padx=(0, 12), pady=8)

        self.playlist_container = ctk.CTkScrollableFrame(self, height=180, fg_color="transparent")
        self.playlist_container.pack(fill="both", expand=True, padx=8, pady=4)

        self.status_label = ctk.CTkLabel(self, textvariable=self.status_var, text_color="gray", font=("Segoe UI", 10))
        self.status_label.pack(pady=(4, 6))

        self.refresh_available()
        self.refresh_playlist()

    def refresh_available(self) -> None:
        options = list_wav_files(self.downloads_dir)
        self.selector.configure(values=options)
        if options:
            if self.selection_var.get() not in options:
                self.selection_var.set(options[0])
            self.add_button.configure(state="normal")
        else:
            self.selection_var.set("")
            self.add_button.configure(state="disabled")

    def refresh_playlist(self) -> None:
        playlist = self.player_manager.get_playlist()
        self._render_playlist(playlist)

    def _render_playlist(self, playlist) -> None:
        for child in self.playlist_container.winfo_children():
            child.destroy()

        current = self.player_manager.get_current_track()
        transport_state = self.player_manager.get_transport_state()
        if not playlist:
            empty = ctk.CTkLabel(self.playlist_container, text="Playlist is empty.", text_color="gray", font=("Segoe UI", 11))
            empty.pack(pady=6, padx=6)
            return

        for track in playlist:
            is_current = bool(current and track.resolve() == current.resolve())
            is_playing = is_current and transport_state == "PLAYING"
            row_color = "#2fa572" if is_playing else "#2b2b2b"
            row = ctk.CTkFrame(self.playlist_container, fg_color=row_color)
            row.pack(fill="x", padx=6, pady=3)

            name_label = ctk.CTkLabel(
                row,
                text=track.stem,
                anchor="w",
                font=("Segoe UI", 11),
                text_color="white" if is_playing else None,
            )
            name_label.pack(side="left", fill="x", expand=True, padx=(8, 6), pady=4)

            if not is_playing:
                play_btn = ctk.CTkButton(
                    row,
                    text="Play",
                    width=70,
                    command=lambda p=track: self._handle_play(p),
                    fg_color="#1db954",
                    hover_color="#169b43",
                )
                play_btn.pack(side="right", padx=(0, 8), pady=4)

            remove_btn = ctk.CTkButton(
                row,
                text="Remove",
                width=80,
                command=lambda p=track: self._handle_remove(p),
            )
            remove_btn.pack(side="right", padx=(0, 8), pady=4)

    def _handle_add(self) -> None:
        selection = self.selection_var.get().strip()
        if not selection:
            self.status_var.set("Select a WAV from downloads first.")
            return

        track_path = self.downloads_dir / f"{selection}.wav"
        try:
            self.player_manager.add_song(track_path)
            self.status_var.set(f"Added to playlist: {selection}")
            self.refresh_playlist()
        except FileNotFoundError:
            self.status_var.set("Selected file was not found.")
        except Exception as exc:
            self.status_var.set(f"Could not add track: {exc}")

    def _handle_remove(self, path: Path) -> None:
        removed = self.player_manager.remove_song(path)
        if removed:
            self.status_var.set(f"Removed from playlist: {path.stem}")
            self.refresh_playlist()
        else:
            self.status_var.set("Track not found in playlist.")

    def _handle_play(self, path: Path) -> None:
        try:
            track = self.player_manager.play_track(path)
            self.status_var.set(f"Playing {track.stem}")
        except Exception as exc:
            self.status_var.set(f"Cannot play track: {exc}")
        self.refresh_playlist()
