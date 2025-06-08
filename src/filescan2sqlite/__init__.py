try:
    from importlib.metadata import version as get_version
except ImportError:  # pragma: no cover
    from importlib_metadata import version as get_version

try:
    __version__ = get_version("filescan2sqlite")
except Exception:  # pragma: no cover
    __version__ = "0.0.1fb"

__all__ = ["__version__"]
