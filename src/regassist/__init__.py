"""Sovereign Regulatory AI Assistant."""

from importlib.metadata import version

__version__ = version("regassist")


def main() -> None:
    """Console entry point; replaced by the real CLI in later stages."""
    print(f"regassist {__version__}")
