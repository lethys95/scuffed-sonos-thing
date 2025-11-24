from threading import Thread
from typing import Dict, List

import customtkinter as ctk

from src.audio import MusicPlayerManager
from src.sqlite_connection import SqliteConnection
from src.sonos import SonosDeviceHandle


class SonosSelectorFrame(ctk.CTkFrame):
    def __init__(self, master, player_manager: MusicPlayerManager, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.player_manager = player_manager
        self.devices: List[SonosDeviceHandle] = []
        self.device_lookup: Dict[str, SonosDeviceHandle] = {}

        self.selection_var = ctk.StringVar()
        self.status_var = ctk.StringVar(value="Discovering Sonos devices...")

        header = ctk.CTkLabel(self, text="Sonos Device", font=("Segoe UI", 16))
        header.pack(pady=(4, 2), padx=8, anchor="w")

        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=8, pady=4)

        self.device_select = ctk.CTkOptionMenu(
            controls,
            variable=self.selection_var,
            values=[],
            command=self._on_device_selected,
            width=240,
        )
        self.device_select.pack(side="left", expand=True, fill="x", padx=(10, 8), pady=8)

        sync_btn = ctk.CTkButton(controls, text="Sync", width=100, command=self._refresh_devices)
        sync_btn.pack(side="right", padx=(0, 10), pady=8)

        status_label = ctk.CTkLabel(self, textvariable=self.status_var, text_color="gray", font=("Segoe UI", 11))
        status_label.pack(pady=(2, 6), padx=8, anchor="w")

        # Initial fetch
        self._refresh_devices(initial=True)

    def _refresh_devices(self, initial: bool = False) -> None:
        self.status_var.set("Discovering Sonos devices..." if initial else "Syncing devices...")
        Thread(target=self._discover_worker, daemon=True).start()

    def _discover_worker(self) -> None:
        try:
            handles = SonosDeviceHandle.discover()
        except Exception as exc:
            error_message = str(exc)
            self.after(0, lambda msg=error_message: self._apply_devices([], error=msg))
            return
        self.after(0, lambda: self._apply_devices(handles, error=None))

    def _apply_devices(self, handles: List[SonosDeviceHandle], error: str | None) -> None:
        self.devices = handles
        self.device_lookup = {h.player_name: h for h in handles}
        options = [h.player_name for h in handles]

        self.device_select.configure(values=options)

        if options:
            preferred = self._load_default_device()
            chosen = preferred if preferred in options else None
            if not chosen:
                chosen = self.selection_var.get() if self.selection_var.get() in options else options[0]
            self.selection_var.set(chosen)
            self.status_var.set(f"Found {len(options)} device(s).")
            self._apply_selection(chosen)
        else:
            self.selection_var.set("")
            self.status_var.set(error or "No Sonos devices found. Click Sync to retry.")

    def _on_device_selected(self, selection: str) -> None:
        if selection:
            self._apply_selection(selection)

    def _apply_selection(self, player_name: str) -> None:
        handle = self.device_lookup.get(player_name)
        if handle:
            try:
                handle.ungroup()
            except Exception as exc:
                self.status_var.set(f"Selected {player_name} (ungroup failed: {exc})")
            self.player_manager.set_device(handle)
            self._persist_default_device(player_name)
            self.status_var.set(f"Selected: {player_name}")

    def _load_default_device(self) -> str | None:
        try:
            with SqliteConnection() as db:
                return db.get_default_device()
        except Exception:
            return None

    def _persist_default_device(self, player_name: str) -> None:
        try:
            with SqliteConnection() as db:
                db.set_default_device(player_name)
        except Exception:
            # Non-fatal; UI should still continue.
            pass
