import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"src"))

from filescan2db.main import scan_directory, setup_db
from filescan2db import __version__
import subprocess
import os



def test_scan_directory(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sample = data_dir / "file.txt"
    sample.write_text("hello")

    db_path = tmp_path / "test.db"
    conn, cur = setup_db(db_path)
    total = scan_directory(str(data_dir), conn, cur, commit_every=1)
    assert total == 1

    cur.execute("SELECT name FROM files")
    assert cur.fetchone()[0] == "file.txt"
    conn.close()


def test_version_cli(tmp_path):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(pathlib.Path(__file__).resolve().parents[1]/"src")
    result = subprocess.run(
        [sys.executable, "-m", "filescan2db", "--version"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.stdout.strip().endswith(__version__)
