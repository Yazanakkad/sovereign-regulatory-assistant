"""Sovereign Regulatory AI Assistant."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("regassist")
except PackageNotFoundError:  # running from a source checkout (the server), not installed
    __version__ = "0.0.0+source"


def main() -> None:
    """Console entry point; replaced by the real CLI in later stages."""
    print(f"regassist {__version__}")
