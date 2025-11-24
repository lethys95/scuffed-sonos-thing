import socket
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Optional


def _best_local_ip() -> str:
    """
    Attempt to find a non-loopback local IP for LAN access.
    Falls back to localhost if detection fails.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Doesn't need to be reachable; used to pick the outbound interface.
            s.connect(("192.0.2.1", 80))
            ip = s.getsockname()[0]
            if not ip.startswith("127."):
                return ip
    except Exception:
        pass

    try:
        host = socket.gethostbyname(socket.gethostname())
        if not host.startswith("127."):
            return host
    except Exception:
        pass

    return "127.0.0.1"


class DownloadHTTPServer:
    """
    Lightweight HTTP server serving a directory for Sonos consumption.
    """

    def __init__(self, directory: str, host: str = "0.0.0.0", port: int = 0) -> None:
        self.directory = directory
        self.bind_host = host
        self.bind_port = port
        self.server: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[Thread] = None
        self.client_host: str = _best_local_ip()
        self.client_port: Optional[int] = None

    @property
    def base_url(self) -> Optional[str]:
        if self.client_port is None:
            return None
        return f"http://{self.client_host}:{self.client_port}"

    def start(self) -> None:
        if self.server:
            return

        handler = partial(SimpleHTTPRequestHandler, directory=self.directory)
        self.server = ThreadingHTTPServer((self.bind_host, self.bind_port), handler)
        self.client_port = self.server.server_port

        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if not self.server:
            return
        self.server.shutdown()
        if self.thread:
            self.thread.join(timeout=2)
        self.server.server_close()
        self.server = None
        self.thread = None
        self.client_port = None


def start_download_server(directory: str, host: str = "0.0.0.0", port: int = 0) -> DownloadHTTPServer:
    server = DownloadHTTPServer(directory=directory, host=host, port=port)
    server.start()
    return server
