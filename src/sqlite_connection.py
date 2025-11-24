import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from src.misc.pathing import ROOT_DIR

DB_PATH = ROOT_DIR / "app.db"


class SqliteConnection:
    """
    Lightweight context manager for SQLite with helper methods for playlists,
    songs, and default device persistence.
    """

    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "SqliteConnection":
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self._ensure_schema()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self.conn:
            return
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
        self.conn = None

    # --- schema & inserts ---
    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                playlist_name TEXT PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS songs (
                path TEXT PRIMARY KEY
            );
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_name TEXT NOT NULL,
                song_path TEXT NOT NULL,
                PRIMARY KEY (playlist_name, song_path),
                FOREIGN KEY (playlist_name) REFERENCES playlists(playlist_name) ON DELETE CASCADE,
                FOREIGN KEY (song_path) REFERENCES songs(path) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS device (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT
            );
            """
        )
        self.conn.commit()

    def add_playlist(self, playlist_name: str) -> None:
        self._require_conn()
        self.conn.execute("INSERT OR IGNORE INTO playlists (playlist_name) VALUES (?)", (playlist_name,))

    def add_song(self, song_path: Path | str) -> None:
        self._require_conn()
        self.conn.execute("INSERT OR IGNORE INTO songs (path) VALUES (?)", (str(Path(song_path).resolve()),))

    def add_song_to_playlist(self, playlist_name: str, song_path: Path | str) -> None:
        """
        Ensure playlist and song exist, then link them.
        """
        self._require_conn()
        song_abs = str(Path(song_path).resolve())
        self.add_playlist(playlist_name)
        self.add_song(song_abs)
        self.conn.execute(
            "INSERT OR IGNORE INTO playlist_songs (playlist_name, song_path) VALUES (?, ?)",
            (playlist_name, song_abs),
        )

    def add_playlist_with_songs(self, playlist_name: str, song_paths: Iterable[Path | str]) -> None:
        self._require_conn()
        self.add_playlist(playlist_name)
        for song in song_paths:
            self.add_song_to_playlist(playlist_name, song)

    # --- maintenance ---
    def remove_missing_song_entries(self) -> int:
        """
        Delete songs (and cascade playlist links) whose files no longer exist.
        Returns count removed.
        """
        self._require_conn()
        cur = self.conn.execute("SELECT path FROM songs")
        paths = [Path(row[0]) for row in cur.fetchall()]
        missing = [p for p in paths if not p.exists()]
        for miss in missing:
            self.conn.execute("DELETE FROM songs WHERE path = ?", (str(miss),))
        return len(missing)

    # --- device persistence ---
    def set_default_device(self, name: str) -> None:
        self._require_conn()
        self.conn.execute(
            """
            INSERT INTO device (id, name) VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name
            """,
            (name,),
        )

    def get_default_device(self) -> Optional[str]:
        self._require_conn()
        cur = self.conn.execute("SELECT name FROM device WHERE id = 1")
        row = cur.fetchone()
        return row[0] if row and row[0] else None

    # --- helpers ---
    def _require_conn(self) -> None:
        if not self.conn:
            raise RuntimeError("Database connection is not open. Use 'with SqliteConnection() as db:'")
