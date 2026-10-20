"""ALN3.5 reference calculations; not an EEG pipeline or a job launcher."""

from .contrasts import ReferenceError, analyze, load_rows

__all__ = ["ReferenceError", "analyze", "load_rows"]
__version__ = "0.1.0"
