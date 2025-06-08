# filescan2db

A small utility to scan a directory tree and store file metadata in a SQLite database.

## Purpose

Record information about regular files (name, size, creation and modification time) and the directories that contain them. Results are stored in a SQLite database for later analysis.

## Features

- Simple command line interface
- Batch commits for good performance
- Error logging with timestamps
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

## Tests

```bash
pytest
```

## License

MIT License
