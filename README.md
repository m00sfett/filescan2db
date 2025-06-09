# filescan2db

A small utility to scan a directory tree and store file metadata in a SQLite database.

## Purpose

Record information about regular files (name, size, creation and modification time) and the directories that contain them. Results are stored in a SQLite database for later analysis.

## Features

- Simple command line interface
- Display program version with `--version`
- Batch commits for good performance
- Error logging with timestamps
- Optional hashing of file contents
- Command to update legacy databases
- Installable via `pyproject.toml`

## Installation

```bash
pip install .
```

Or for development:

```bash
git clone <repo-url>
cd filescan2db
pip install -e .
```

## Usage

```bash
python -m filescan2db <directory>
```

See `filescan2db --help` for optional arguments.
Use `filescan2db --version` to display the current version.

### Hashing

Optional hashing of files is enabled with `--hash`. Provide a comma separated
list of algorithms or omit the value to choose interactively.

Supported algorithms:

- `md5` – requires the Python `hashlib` module (built-in)
- `sha1` – built-in via `hashlib`
- `sha256` – built-in via `hashlib`
- `sha3` – SHA3-256, built-in via `hashlib`
- `blake3` – requires the optional `blake3` package
- `xxhash_32` – requires the optional `xxhash` package
- `xxhash_64` – requires the optional `xxhash` package
- `xxhash_128` – requires the optional `xxhash` package

If a library is missing, the corresponding hash will be skipped and an error is
reported.

## Tests

```bash
pytest
```

See `CHANGELOG.md` for release notes.

## License

MIT License
