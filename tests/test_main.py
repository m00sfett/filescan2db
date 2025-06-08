import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/"src"))

from filescan2sqlite.main import scan_directory, setup_db


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
