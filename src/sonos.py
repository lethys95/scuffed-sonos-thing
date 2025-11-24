from dataclasses import dataclass
from typing import Any, Iterable, List, Optional

from soco import discover


@dataclass
class SonosDeviceHandle:
    player_name: str
    sonos: Any

    @staticmethod
    def from_device(device: Any) -> "SonosDeviceHandle":
        return SonosDeviceHandle(player_name=device.player_name, sonos=device)

    @staticmethod
    def discover() -> List["SonosDeviceHandle"]:
        devices = discover() or set()
        handles = [SonosDeviceHandle.from_device(d) for d in devices]
        return sorted(handles, key=lambda h: h.player_name)

    @staticmethod
    def find_by_name(name: str, handles: Iterable["SonosDeviceHandle"]) -> Optional["SonosDeviceHandle"]:
        for handle in handles:
            if handle.player_name == name:
                return handle
        return None

    # Volume controls
    def get_volume(self) -> int:
        try:
            return int(self.sonos.volume)
        except Exception as exc:
            raise RuntimeError(f"Unable to fetch volume: {exc}") from exc

    def set_volume(self, volume: int) -> int:
        clamped = max(0, min(100, int(volume)))
        try:
            self.sonos.volume = clamped
        except Exception as exc:
            raise RuntimeError(f"Unable to set volume: {exc}") from exc
        return clamped

    def change_volume(self, delta: int) -> int:
        current = self.get_volume()
        return self.set_volume(current + delta)

    # Group management
    def ungroup(self) -> None:
        """
        Ensure this device leaves any existing group to avoid multi-room playback.
        """
        try:
            # SoCo exposes unjoin(), which calls BecomeCoordinatorOfStandaloneGroup.
            if hasattr(self.sonos, "unjoin"):
                self.sonos.unjoin()
            else:
                raise AttributeError("unjoin not available on SoCo device")
        except Exception as exc:
            raise RuntimeError(f"Unable to ungroup device: {exc}") from exc
