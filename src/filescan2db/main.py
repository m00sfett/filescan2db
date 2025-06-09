"""Command-line interface for filescan2db"""
from __future__ import annotations

import argparse
import os
import sqlite3
import time
from typing import Dict, Iterable, Optional
from datetime import datetime

from . import __version__

DB_NAME = "files.db"
LOG_NAME = "filescan2db_errors.log"
COMMIT_EVERY = 10000

HASH_ALGOS = [
    "xxhash_32",
    "xxhash_64",
    "xxhash_128",
    "md5",
    "sha1",
    "sha256",
    "sha3",
    "blake3",
]


ERRORS: list[str] = []


def log_error(message: str) -> None:
    """Record an error and print it to the console."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{timestamp} ERROR: {message}"
    ERRORS.append(line)
    print(line)


def flush_errors(log_file: str, overwrite: bool = False, suppress: bool = False) -> None:
    """Write collected errors to log file if any exist."""
    if suppress or not ERRORS:
        return
    mode = "w" if overwrite else "a"
    with open(log_file, mode) as fh:
        fh.write("\n".join(ERRORS) + "\n")


def update_db(db_path: str, *, safe: bool = False) -> None:
    """Add missing hash columns to an existing database."""
    if safe and os.path.exists(db_path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = f"{db_path}.{ts}.backup"
        import shutil

        shutil.copy(db_path, backup)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(files)")
    existing = {row[1] for row in cur.fetchall()}
    added = False
    for algo in HASH_ALGOS:
        if algo not in existing:
            cur.execute(f"ALTER TABLE files ADD COLUMN {algo} TEXT")
            added = True
    if added:
        conn.commit()
    conn.close()


def compute_hashes(path: str, algorithms: Iterable[str]) -> Dict[str, Optional[str]]:
    """Return hex digests for the given algorithms."""
    results: Dict[str, Optional[str]] = {algo: None for algo in HASH_ALGOS}
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except Exception as exc:  # pragma: no cover - log and skip
        log_error(f"Failed to read '{path}': {exc}")
        return results

    for algo in algorithms:
        try:
            lower = algo.lower()
            if lower == "md5":
                import hashlib

                results[algo] = hashlib.md5(data).hexdigest()
            elif lower == "sha1":
                import hashlib

                results[algo] = hashlib.sha1(data).hexdigest()
            elif lower == "sha256":
                import hashlib

                results[algo] = hashlib.sha256(data).hexdigest()
            elif lower == "sha3":
                import hashlib

                results[algo] = hashlib.sha3_256(data).hexdigest()
            elif lower == "blake3":
                try:
                    import blake3

                    results[algo] = blake3.blake3(data).hexdigest()
                except Exception as exc:  # pragma: no cover
                    log_error(f"blake3 unavailable: {exc}")
            elif lower == "xxhash_32":
                try:
                    import xxhash

                    results[algo] = xxhash.xxh32(data).hexdigest()
                except Exception as exc:  # pragma: no cover
                    log_error(f"xxhash unavailable: {exc}")
            elif lower == "xxhash_64":
                try:
                    import xxhash

                    results[algo] = xxhash.xxh64(data).hexdigest()
                except Exception as exc:  # pragma: no cover
                    log_error(f"xxhash unavailable: {exc}")
            elif lower == "xxhash_128":
                try:
                    import xxhash

                    results[algo] = xxhash.xxh3_128(data).hexdigest()
                except Exception as exc:  # pragma: no cover
                    log_error(f"xxhash unavailable: {exc}")
        except Exception as exc:  # pragma: no cover - unexpected failure
            log_error(f"Hash error for {path} with {algo}: {exc}")
    return results


def setup_db(db_path: str = DB_NAME) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    """Initialise or open a SQLite database and ensure schema."""
    create_new = not os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("PRAGMA synchronous = NORMAL;")
    if create_new:
        cur.execute(
            """
            CREATE TABLE paths (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE
            );
            """
        )
        columns = [
            "id INTEGER PRIMARY KEY AUTOINCREMENT",
            "path_id INTEGER",
            "name TEXT",
            "size INTEGER",
            "ctime INTEGER",
            "mtime INTEGER",
        ]
        for algo in HASH_ALGOS:
            columns.append(f"{algo} TEXT")
        cur.execute(
            f"CREATE TABLE files ({','.join(columns)}, FOREIGN KEY(path_id) REFERENCES paths(id));"
        )
        conn.commit()
    else:
        update_db(db_path)
    return conn, cur


def scan_directory(
    root_dir: str,
    conn: sqlite3.Connection,
    cur: sqlite3.Cursor,
    *,
    commit_every: int = COMMIT_EVERY,
    hash_algos: Optional[Iterable[str]] = None,
) -> int:
    """Scan ``root_dir`` and insert file metadata into the database."""
    path_cache: Dict[str, int] = {}
    file_count = 0
    hash_algos = [a.lower() for a in (hash_algos or []) if a.lower() in HASH_ALGOS]

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
                query = (
                    f"SELECT size, ctime, mtime"
                    + ("," + ",".join(hash_algos) if hash_algos else "")
                    + " FROM files WHERE path_id=? AND name=? AND size=? AND ctime=? AND mtime=?"
                )
                params = (
                    parent_id,
                    name,
                    st.st_size,
                    int(st.st_ctime),
                    int(st.st_mtime),
                )
                cur.execute(query, params)
                existing = cur.fetchone()

                if existing:
                    missing = []
                    for idx, algo in enumerate(hash_algos or [], start=3):
                        if existing[idx] is None:
                            missing.append(algo)
                    if missing:
                        hashes = compute_hashes(full, missing)
                        assignments = ",".join(f"{algo}=?" for algo in missing)
                        sql = (
                            f"UPDATE files SET {assignments}"
                            " WHERE path_id=? AND name=? AND size=? AND ctime=? AND mtime=?"
                        )
                        cur.execute(sql, [hashes.get(a) for a in missing] + list(params))
                    continue

                hashes = compute_hashes(full, hash_algos) if hash_algos else {}
                columns = ["path_id", "name", "size", "ctime", "mtime"] + (hash_algos if hash_algos else [])
                placeholders = ",".join(["?"] * len(columns))
                sql = f"INSERT INTO files({','.join(columns)}) VALUES({placeholders})"
                values = [
                    parent_id,
                    name,
                    st.st_size,
                    int(st.st_ctime),
                    int(st.st_mtime),
                ]
                for algo in hash_algos:
                    values.append(hashes.get(algo))
                cur.execute(sql, tuple(values))
                file_count += 1
            except Exception as exc:  # pragma: no cover - log and skip
                log_error(f"Error processing '{full}': {exc}")
                continue

            if file_count % commit_every == 0:
                conn.commit()

    conn.commit()
    return file_count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Return parsed command line arguments."""

    parser = argparse.ArgumentParser(
        description="Recursively scan a directory and store file metadata in SQLite",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("path", help="Directory to scan")
    parser.add_argument(
        "--db",
        default=DB_NAME,
        help="Output SQLite database file",
    )
    parser.add_argument(
        "--log",
        default=LOG_NAME,
        help="Log file for errors",
    )
    parser.add_argument(
        "--hash",
        nargs="?",
        const="interactive",
        help="Enable hashing. Provide comma separated algorithms or use without value for interactive selection",
    )
    parser.add_argument(
        "-u",
        "--updatedb",
        metavar="DBASE",
        help="Update existing database to include hash columns",
    )
    parser.add_argument(
        "--safe",
        action="store_true",
        help="Create a backup copy when updating a database",
    )
    parser.add_argument("-l", action="store_true", help="Suppress log file creation")
    parser.add_argument("-fo", action="store_true", help="Force overwrite of the log file")
    parser.add_argument("-fa", action="store_true", help="Force append to the log file without prompts")
    parser.add_argument(
        "--commit-every",
        type=int,
        default=COMMIT_EVERY,
        help="Commit after processing this many files",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface and return an exit status."""

    args = parse_args(argv)
    target = args.path

    if not os.path.isdir(target):
        print(f"Error: '{target}' is not a directory.")
        return 2

    if args.updatedb:
        update_db(args.updatedb, safe=args.safe)
        print("Database updated")
        return 0

    conn, cur = setup_db(args.db)

    start = time.time()
    if args.hash == "interactive":
        print("Available algorithms: " + ", ".join(HASH_ALGOS))
        user = input("Algorithms (comma separated): ")
        hash_list = [a.strip() for a in user.split(",") if a.strip()]
    elif args.hash:
        hash_list = [a.strip() for a in args.hash.split(",") if a.strip()]
    else:
        hash_list = []

    total = scan_directory(
        target,
        conn,
        cur,
        commit_every=args.commit_every,
        hash_algos=hash_list,
    )
    duration = time.time() - start
    print(f"Done: scanned {total} files in {duration:.1f} s.")
    flush_errors(args.log, overwrite=args.fo, suppress=args.l and not args.fa)
    if ERRORS:
        print(f"{len(ERRORS)} errors logged")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
