"""Command-line interface for filescan2sqlite."""
from __future__ import annotations

import argparse
import logging
import os
import sqlite3
import time
from typing import Dict

DB_NAME = "files.db"
LOG_NAME = "error.log"
COMMIT_EVERY = 10000


def setup_logging(log_file: str = LOG_NAME) -> None:
    """Configure basic logging to the given file."""
    logging.basicConfig(
        filename=log_file,
        filemode="a",
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )


def setup_db(db_path: str = DB_NAME) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    """Initialise a fresh SQLite database."""
    if os.path.exists(db_path):
        os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("PRAGMA synchronous = NORMAL;")
    cur.execute(
        """
        CREATE TABLE paths (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE files (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            path_id INTEGER,
            name    TEXT,
            size    INTEGER,
            ctime   INTEGER,
            mtime   INTEGER,
            FOREIGN KEY(path_id) REFERENCES paths(id)
        );
        """
    )
    conn.commit()
    return conn, cur


def scan_directory(
    root_dir: str,
    conn: sqlite3.Connection,
    cur: sqlite3.Cursor,
    *,
    commit_every: int = COMMIT_EVERY,
) -> int:
    """Scan ``root_dir`` and insert file metadata into the database."""
    path_cache: Dict[str, int] = {}
    file_count = 0

    for root, _dirs, files in os.walk(root_dir, followlinks=False):
        if root not in path_cache:
            try:
                cur.execute("INSERT OR IGNORE INTO paths(path) VALUES(?)", (root,))
                cur.execute("SELECT id FROM paths WHERE path = ?", (root,))
                path_cache[root] = cur.fetchone()[0]
            except Exception as exc:  # pragma: no cover - log and skip
                logging.error("DB error for path %s: %s", root, exc)
                continue

        parent_id = path_cache[root]
        for name in files:
            full = os.path.join(root, name)
            if not os.path.isfile(full) or os.path.islink(full):
                continue
            try:
                st = os.stat(full)
                cur.execute(
                    "INSERT INTO files(path_id, name, size, ctime, mtime) VALUES(?,?,?,?,?)",
                    (
                        parent_id,
                        name,
                        st.st_size,
                        int(st.st_ctime),
                        int(st.st_mtime),
                    ),
                )
                file_count += 1
            except Exception as exc:  # pragma: no cover - log and skip
                logging.error("Error processing '%s': %s", full, exc)
                continue

            if file_count % commit_every == 0:
                conn.commit()

    conn.commit()
    return file_count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Recursively scan a directory and store file metadata in SQLite",
    )
    parser.add_argument("path", help="Directory to scan")
    parser.add_argument(
        "--db",
        default=DB_NAME,
        help=f"Output SQLite database file (default: {DB_NAME})",
    )
    parser.add_argument(
        "--log",
        default=LOG_NAME,
        help=f"Log file for errors (default: {LOG_NAME})",
    )
    parser.add_argument(
        "--commit-every",
        type=int,
        default=COMMIT_EVERY,
        help="Commit after processing this many files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.path

    if not os.path.isdir(target):
        print(f"Fehler: '{target}' ist kein Verzeichnis.")
        return 2

    setup_logging(args.log)
    conn, cur = setup_db(args.db)

    start = time.time()
    total = scan_directory(target, conn, cur, commit_every=args.commit_every)
    duration = time.time() - start
    print(f"Fertig: {total} Dateien in {duration:.1f} s gescannt.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
