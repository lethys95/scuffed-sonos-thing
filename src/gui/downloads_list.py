from pathlib import Path
from typing import Iterable, List

import customtkinter as ctk


def list_wav_files(downloads_dir: Path) -> List[str]:
    """
    Return WAV filenames (without extension) from the downloads directory.
    """
    if not downloads_dir.exists():
        return []
    return sorted(
        [p.stem for p in downloads_dir.iterdir() if p.is_file() and p.suffix.lower() == ".wav"]
    )


class DownloadsListFrame(ctk.CTkFrame):
    def __init__(self, master, downloads_dir: Path, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.downloads_dir = downloads_dir
        header = ctk.CTkLabel(self, text="Available WAV files", font=("Segoe UI", 14))
        header.pack(pady=(4, 2))

        self._list_container = ctk.CTkScrollableFrame(self, height=180, fg_color="transparent")
        self._list_container.pack(fill="both", expand=True, padx=8, pady=4)
        self.refresh_button = ctk.CTkButton(self, text="Refresh", command=self.refresh, width=100)
        self.refresh_button.pack(pady=(4, 8))

        self._empty_label = ctk.CTkLabel(self._list_container, text="No WAV files found.", text_color="gray", font=("Segoe UI", 11))
        self.refresh()

    def _render_list(self, items: Iterable[str]) -> None:
        # Clear old items
        for child in self._list_container.winfo_children():
            child.destroy()

        entries = list(items)
        if not entries:
            self._empty_label = ctk.CTkLabel(self._list_container, text="No WAV files found.", text_color="gray", font=("Segoe UI", 11))
            self._empty_label.pack(pady=6, padx=6)
            return

        for name in entries:
            row = ctk.CTkLabel(self._list_container, text=name, anchor="w", font=("Segoe UI", 11))
            row.pack(fill="x", padx=6, pady=3)

    def refresh(self) -> None:
        files = list_wav_files(self.downloads_dir)
        self._render_list(files)
