import customtkinter as ctk

from src.audio import MusicPlayerManager


class AudioLevelControls(ctk.CTkFrame):
    def __init__(self, master, player_manager: MusicPlayerManager, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self.player_manager = player_manager
        self.volume_var = ctk.StringVar(value="Volume: --")

        header = ctk.CTkLabel(self, text="Volume", font=("Segoe UI", 14))
        header.pack(pady=(4, 2))

        content = ctk.CTkFrame(self)
        content.pack(fill="x", padx=8, pady=6)
        content.grid_columnconfigure((0, 1, 2), weight=1, uniform="volgrid")

        minus_btn = ctk.CTkButton(content, text="-", width=60, command=lambda: self._change(-5))
        minus_btn.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        vol_label = ctk.CTkLabel(content, textvariable=self.volume_var, anchor="center", font=("Segoe UI", 12))
        vol_label.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        plus_btn = ctk.CTkButton(content, text="+", width=60, command=lambda: self._change(5))
        plus_btn.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        self.refresh_volume()

    def refresh_volume(self) -> None:
        vol = self.player_manager.get_volume()
        if vol is None:
            self.volume_var.set("Volume: --")
        else:
            self.volume_var.set(f"Volume: {vol}%")

    def _change(self, delta: int) -> None:
        try:
            new_vol = self.player_manager.change_volume(delta)
        except Exception as exc:
            self.volume_var.set(f"Volume error: {exc}")
            return

        if new_vol is not None:
            self.volume_var.set(f"Volume: {new_vol}%")
        else:
            self.volume_var.set("Volume: --")
