import customtkinter as ctk

from src.audio import AudioDownloadManager, DOWNLOADS_DIR, MusicPlayerManager, ensure_downloads_dir, is_valid_url
from src.gui.audio_level_controls import AudioLevelControls
from src.gui.downloads_list import DownloadsListFrame
from src.gui.playlist_control_panel import PlaylistControlPanel
from src.gui.playlist_manager import PlaylistManagerFrame
from src.gui.sonos_selector import SonosSelectorFrame


class SonosAppThing(ctk.CTk):
    def __init__(self, stream_base_url: str | None = None) -> None:
        super().__init__()
        self.title("Sonos Thing")
        self.geometry("900x780")
        self.resizable(False, False)

        self.url_var = ctk.StringVar()
        self.status_var = ctk.StringVar(value="Enter a URL to download audio as WAV.")
        self.downloader = AudioDownloadManager.instance()
        self.player_manager = MusicPlayerManager.instance()
        self.downloads_list: DownloadsListFrame | None = None
        self.playlist_frame: PlaylistManagerFrame | None = None
        self.control_panel: PlaylistControlPanel | None = None

        ensure_downloads_dir()
        if stream_base_url:
            self.player_manager.set_stream_base_url(stream_base_url)
        self._last_playback_signature: tuple | None = None

        self._build_content()
        self._schedule_polling()

    def _build_content(self) -> None:
        header = ctk.CTkLabel(self, text="Sonos Thing", font=("Segoe UI", 22))
        header.pack(padx=24, pady=(18, 8), anchor="center")

        self.tabs = ctk.CTkTabview(self, width=860, height=640, command=self._on_tab_change)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        download_tab = self.tabs.add("Audio download")
        device_tab = self.tabs.add("Device")
        play_tab = self.tabs.add("Play")

        # Download tab
        entry_frame = ctk.CTkFrame(download_tab)
        entry_frame.pack(fill="x", padx=24, pady=(16, 10))

        url_entry = ctk.CTkEntry(
            entry_frame,
            textvariable=self.url_var,
            width=320,
            placeholder_text="https://example.com/track",
        )
        url_entry.pack(side="left", expand=True, fill="x", padx=(16, 8), pady=12)

        submit_button = ctk.CTkButton(
            entry_frame,
            text="Submit",
            command=self._handle_submit,
            width=110,
        )
        submit_button.pack(side="right", padx=(0, 16), pady=12)

        status_label = ctk.CTkLabel(
            download_tab,
            textvariable=self.status_var,
            text_color="gray",
            font=("Segoe UI", 12),
            wraplength=560,
            justify="left",
        )
        status_label.pack(fill="x", padx=24, pady=(4, 12))

        self.downloads_list = DownloadsListFrame(download_tab, downloads_dir=DOWNLOADS_DIR)
        self.downloads_list.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        downloads_path_label = ctk.CTkLabel(
            download_tab,
            text=f"Downloads folder: {DOWNLOADS_DIR}",
            text_color="gray",
            font=("Segoe UI", 11),
            wraplength=640,
            justify="left",
        )
        downloads_path_label.pack(fill="x", padx=24, pady=(0, 8))

        # Device tab
        sonos_frame = SonosSelectorFrame(device_tab, player_manager=self.player_manager)
        sonos_frame.pack(fill="x", padx=24, pady=(24, 12))

        # Play tab
        self.playlist_frame = PlaylistManagerFrame(
            play_tab,
            downloads_dir=DOWNLOADS_DIR,
            player_manager=self.player_manager,
        )
        self.playlist_frame.pack(fill="both", expand=True, padx=24, pady=(16, 8))

        self.control_panel = PlaylistControlPanel(
            play_tab,
            player_manager=self.player_manager,
            on_change=self._on_playback_change,
        )
        self.control_panel.pack(fill="x", padx=24, pady=(0, 12))

        self.audio_levels = AudioLevelControls(play_tab, player_manager=self.player_manager)
        self.audio_levels.pack(fill="x", padx=24, pady=(0, 12))

        close_button = ctk.CTkButton(self, text="Close", command=self.destroy)
        close_button.pack(pady=(0, 12))

    def _handle_submit(self) -> None:
        url = self.url_var.get().strip()
        if not is_valid_url(url):
            self.status_var.set("Please enter a valid http/https URL.")
            return

        self.status_var.set("Downloading...")
        self.downloader.enqueue(url, on_complete=self._on_download_complete)

    def _on_download_complete(self, url: str, path, error) -> None:
        # Run UI updates on the main thread.
        def _update_ui() -> None:
            if error:
                self.status_var.set(f"Download failed; removed from queue. ({error})")
            elif path:
                self.status_var.set(f"Saved to downloads/{path.name}")
                self.url_var.set("")
            else:
                self.status_var.set("Download finished.")

            if self.downloads_list:
                self.downloads_list.refresh()
            if self.playlist_frame:
                self.playlist_frame.refresh_available()
                self.playlist_frame.refresh_playlist()

        self.after(0, _update_ui)

    def _start_http_server(self) -> None:
        pass

    def _on_playback_change(self, _track) -> None:
        if self.playlist_frame:
            self.playlist_frame.refresh_playlist()

    def _on_tab_change(self, tab_name: str | None = None) -> None:
        # CustomTkinter tabview command provides no args; use current selection when absent.
        current = tab_name or (self.tabs.get() if hasattr(self, "tabs") else None)
        if current == "Play":
            if self.playlist_frame:
                self.playlist_frame.refresh_available()
                self.playlist_frame.refresh_playlist()
            if hasattr(self, "audio_levels") and self.audio_levels:
                try:
                    self.audio_levels.refresh_volume()
                except Exception:
                    pass

    def _schedule_polling(self) -> None:
        self.after(1000, self._poll_playback)

    def _poll_playback(self) -> None:
        current_track = None
        transport_state = None
        try:
            self.player_manager.poll_and_maybe_advance()
            current_track = self.player_manager.get_current_track()
            transport_state = self.player_manager.get_transport_state()
        except Exception:
            pass

        signature = (
            str(current_track.resolve()) if current_track else None,
            transport_state,
        )
        if signature != self._last_playback_signature:
            self._last_playback_signature = signature
            if self.playlist_frame:
                try:
                    self.playlist_frame.refresh_playlist()
                except Exception:
                    pass

        # Continue polling
        self._schedule_polling()


def run_application() -> None:
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    # Stream base URL should be set before instantiating if provided via main.
    app = SonosAppThing(stream_base_url=MusicPlayerManager.instance().stream_base_url)
    app.mainloop()
