"""
Utility modules for votuderep
==============================

This package contains utility functions and helpers for votuderep,
including file I/O, validation, and logging functionality.

Available utility modules:

- `votuderep.utils.io`: FASTA file reading and writing utilities
- `votuderep.utils.validators`: Input validation and external tool checking
- `votuderep.utils.logging`: Logging configuration with rich output formatting
"""

# Import modules for documentation
from . import io, logging, validators

# Import functions for API
from .validators import check_blastn, validate_file_exists
from .io import read_fasta, write_fasta, filter_sequences
from .logging import setup_logger, get_logger

__all__ = [
    # Modules (for pdoc)
    "io",
    "logging",
    "validators",
    # Functions (for API)
    "check_blastn",
    "validate_file_exists",
    "read_fasta",
    "write_fasta",
    "filter_sequences",
    "setup_logger",
    "get_logger",
]
