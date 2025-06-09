# AGENTS.md — Prompt Specification for Codex (filescan2db Extension)

## Objective

Enhance the `filescan2db` tool according to the KISS principle. The tool should provide an intuitive, easy-to-use command line interface and support optional hashing of scanned files. This will create version 0.3.0.

## Enhancements

### General

* Adhere strictly to the **KISS (Keep It Simple, Stupid)** principle.
* Add a **verbose description of all hash algorithms and their dependencies** to the `README.md`.
* Ensure a clean and logical CLI layout with minimal user friction.

### Hashing

* Add CLI option `--hash ALGO` or `--hash ALGO1,ALGO2,...`

  * Enables hashing for each scanned file.
  * User input is case-insensitive.
  * Supported algorithms:

    * `xxhash_64`
    * `xxhash_128`
    * `md5`
    * `sha1`
    * `sha256`
    * `sha3`
    * `blake3`

### Database

* Add **one column per hash algorithm** to the database schema.
* Support legacy databases:

  * Command: `filescan2db --updatedb DBASE` or `filescan2db -u DBASE`
  * Adds missing hash columns (initialized as NULL or empty).
  * Prompts user before modifying the original database.
  * Automatically prompt for update if legacy DB is reused in a scan.
  * Optional flag `--safe`:

    * Creates a backup copy of the old database (name format: `DBASE.YYYYMMDD_HHMMSS.backup`)

### Logging

* Log file name: `filescan2db_errors.log`
* Behavior:

  * Do not create the log if there are no errors.
  * If errors occur, append to the existing log or create a new one.
  * Display all errors also in the console.
  * At the end of a run, print a summary of errors (if any).
* Logging options:

  * `-l` suppresses log file creation.
  * `-fo` forces overwrite of the log file.
  * `-fa` forces append mode with no interactive questions.

### CLI Examples

The CLI must behave as shown below. In case of internal conflicts, this section takes precedence.

```shell
# Default usage: nothing or only directory provided
python -m filescan2db
# → DIR is current directory.
python -m filescan2db DIR
# → Recursively scans DIR
# → Prompts user where to create 'files.db':
#     [1] inside DIR (default)
#     [2] in current working directory
#     [3] custom user path
# → If 'files.db' already exists:
#     → with hash columns: integrate results
#     → without hash columns: update DB first

# Specify custom database file
python -m filescan2db DIR DBASE
# → Uses DBASE as database path
# → Skips interactive DB prompts

# Suppress error log completely
python -m filescan2db -l

# Force overwrite of error log, suppress questions
python -m filescan2db DIR DBASE -fo

# Force append to error log, suppress questions
python -m filescan2db DIR DBASE -fa

# Enable hashing with interactive algorithm selection
python -m filescan2db DIR --hash
# → User selects one or more algorithms (multi-choice)

# Enable hashing with specific algorithms
python -m filescan2db DIR --hash md5,xxhash_64
# → Uses specified algorithms without further prompt
```

### Additional Notes

* If a hash function fails for a file, that file is skipped.

  * Error is printed immediately in console and logged.
* CLI argument parsing should be robust against malformed or unknown algorithms.

End of specification.
