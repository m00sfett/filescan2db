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

## Hashing

Optional hashing of file contents is enabled with the `--hash` option. You may provide a comma-separated list of algorithms (e.g., `--hash=md5,sha256`), or omit the value to choose interactively.

Hashing is useful for detecting file duplicates, verifying data integrity, or comparing file versions across snapshots. However, depending on the file count and size, hashing can significantly affect performance. Choosing the right algorithm is crucial.

### Supported Algorithms

The following hashing algorithms are supported:

| Algorithm     | Source         | Relative Speed¹ | Notes |
|---------------|----------------|------------------|-------|
| `xxhash_64`   | `xxhash`       | 🟢 **Fastest**    | Very fast non-cryptographic hash with low collision rate for general file scanning. Ideal for large batches. |
| `xxhash_128`  | `xxhash`       | 🟢 Fast           | Larger output, slightly slower than `xxhash_64`. |
| `xxhash_32`   | `xxhash`       | 🟢 Fast           | Smaller output, slightly higher collision risk than 64/128 variants. |
| `blake3`      | `blake3`       | 🟡 Fast (~SHA256) | Cryptographic hash with SIMD acceleration; fast and secure. Good balance for integrity verification. |
| `md5`         | `hashlib`      | 🟡 Medium         | Fast but considered broken for security; still widely used for checksum comparison. |
| `sha1`        | `hashlib`      | 🟡 Medium         | Better than MD5, but cryptographically weak. |
| `sha256`      | `hashlib`      | 🔴 Slower         | Strong cryptographic hash; slower but very collision-resistant. |
| `sha3`        | `hashlib`      | 🔴 Slowest        | High security, but slower and less commonly used in performance-critical scenarios. |

¹ Relative speed estimated for real-world workloads:
- 70% of space large files (>100 MB)
- 20% of space medium files (1–100 MB)
- 10% of space many small files (<1 MB)

### Recommendations by Use Case

| Use Case                     | Recommended Hashes     | Rationale |
|-----------------------------|------------------------|-----------|
| **Fast scans, low CPU use** | `xxhash_64` or `xxhash_128` | Extremely fast, very low CPU impact, sufficient for non-secure deduplication. |
| **Data integrity check**    | `blake3`, `sha256`     | Cryptographic security, supports verification over time. |
| **Legacy compatibility**    | `md5`, `sha1`          | If systems expect these hashes (e.g., for checksums), despite security concerns. |

### Collisions

Non-cryptographic hashes like `xxhash` are fast but have a higher theoretical collision risk. For file comparison or deduplication in trusted local environments, the risk is negligible. For cryptographic guarantees (e.g. anti-tamper, secure storage), use `blake3` or `sha256`.

> If a required library is missing (e.g. `xxhash` or `blake3`), the corresponding hash algorithm is skipped and a warning is logged.

## Tests

```bash
pytest
```

See `CHANGELOG.md` for release notes.

## License

MIT License
