from src.audio import MusicPlayerManager, ensure_downloads_dir
from src.gui.gui import run_application
from src.misc.http_server import start_download_server
from src.sonos import SonosDeviceHandle



def main() -> None:
    #sonos_one = SonosDeviceHandle.discover_and_select()
    #sonos_two = SonosDeviceHandle.discover_and_select()

    #coordinator = sonos_one.sonos.group.coordinator
    #sonos_two.sonos.join(coordinator)

    #coordinator.play_uri("https://music.youtube.com/watch?v=2WPCLda_erI")

    #sonos_one.sonos.play_uri("https://music.youtube.com/watch?v=2WPCLda_erI")
    ensure_downloads_dir()
    server = start_download_server(str(ensure_downloads_dir()))
    if server.base_url:
        MusicPlayerManager.instance().set_stream_base_url(server.base_url)

    run_application()


if __name__ == "__main__":
    main()
