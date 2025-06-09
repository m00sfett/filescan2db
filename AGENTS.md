# AGENTS.md

## Purpose

This document defines how automated agents (e.g., Codex, Copilot, ChatGPT)
should behave when contributing to this codebase. It provides coding
conventions, architectural principles, and generation rules to ensure
consistency, maintainability, and alignment with project goals.

---

## General instructions

- Discard lines in triple parentheses `((( ... )))` as they are placeholders for project-specific information.

## Project Context

((( - **Language:** Python ≥ 3.9 )))

- **Style:** Functional and modular; KISS-style.
- **Structure:** `src/` layout with `pyproject.toml`
- **Tests:** `pytest` under `tests/`

---

## Agent Behavior

### 1. Comments & Style

- Use **English comments and docstrings**.
- Follow [PEP 8](https://peps.python.org/pep-0008/) and format with **Black**.
- Use Google-style docstrings, for example:

```python
def foo(bar: str) -> int:
    """
    Example summary.

    Args:
        bar (str): Input string.

    Returns:
        int: Processed result.
    """
```

### 2. Versioning

- Define the version **only** in `pyproject.toml`.
- Use `importlib.metadata.version("module_name")` for runtime access.

### 3. Logging

- Never use `print()` in production code.
- Use the `logging` module with configurable levels.
- Initialize `logger = logging.getLogger(__name__)` per module.

### 4. File System

- Avoid hardcoded or absolute paths.
- Use `pathlib.Path` instead of `os.path`.

### 5. Tests

- Always write tests for new functions.
- Use `pytest.mark.parametrize` when applicable.
- Mock external services using `unittest.mock`.

---

## Agent Permissions

### Allowed

- Extract reusable helpers if logic is duplicated.
- Organize helper logic into `utils.py` or `helpers/`.
- Add explanatory comments for unclear decisions.

### Not allowed

- Introduce new dependencies without inline justification.
- Skip writing tests because the function is "simple".
- Perform file read/write operations without confirmation.
- Introduce global state unless required by the CLI.

---

## Context & Reference

> When in doubt, follow patterns from existing modules (e.g., `src/projectname/features.py`).  
> Experimental code in experimental/ does not need to meet all compliance standards,
  but must be clearly marked and omitted from releases.

---

## Miscellaneous

- All changelogs must go to `CHANGELOG.md`. Newest changes first.
- Use `# TODO:` for unfinished code.
- Apply modern `typing` annotations (`list[int]` over `List[int]` for Python ≥3.9).
