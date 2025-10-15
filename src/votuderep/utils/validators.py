"""Validation utilities for checking external tools and file existence."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


class VotuDerepError(Exception):
    """Base exception for votuderep errors."""

    pass


class BlastnNotFoundError(VotuDerepError):
    """Exception raised when blastn is not found in PATH."""

    pass


class FileValidationError(VotuDerepError):
    """Exception raised when file validation fails."""

    pass


def check_blastn(custom_path: Optional[str] = None) -> str:
    """
    Check if blastn is available in PATH or at custom location.

    Args:
        custom_path: Optional custom path to blastn executable

    Returns:
        Path to blastn executable

    Raises:
        BlastnNotFoundError: If blastn is not found
    """
    # Check custom path first
    if custom_path:
        if os.path.isfile(custom_path) and os.access(custom_path, os.X_OK):
            return custom_path
        raise BlastnNotFoundError(f"blastn not found at specified path: {custom_path}")

    # Check environment variable
    env_path = os.environ.get("VOTUDEREP_BLASTN_PATH")
    if env_path:
        if os.path.isfile(env_path) and os.access(env_path, os.X_OK):
            return env_path
        raise BlastnNotFoundError(f"blastn not found at VOTUDEREP_BLASTN_PATH: {env_path}")

    # Check PATH
    blastn_path = shutil.which("blastn")
    if blastn_path:
        return blastn_path

    # Not found anywhere
    raise BlastnNotFoundError(
        "blastn not found in PATH. Please install BLAST+ toolkit.\n"
        "Installation instructions:\n"
        "  - Conda: conda install -c bioconda blast\n"
        "  - Ubuntu/Debian: apt-get install ncbi-blast+\n"
        "  - MacOS: brew install blast\n"
        "  - Or download from: https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastDocs&DOC_TYPE=Download\n"
        "Alternatively, set VOTUDEREP_BLASTN_PATH environment variable."
    )


def get_blastn_version(blastn_path: str) -> str:
    """
    Get blastn version string.

    Args:
        blastn_path: Path to blastn executable

    Returns:
        Version string

    Raises:
        VotuDerepError: If version check fails
    """
    try:
        result = subprocess.run(
            [blastn_path, "-version"], capture_output=True, text=True, check=True
        )
        # Extract version from output (e.g., "blastn: 2.13.0+")
        version_line = result.stdout.strip().split("\n")[0]
        return version_line
    except subprocess.CalledProcessError as e:
        raise VotuDerepError(f"Failed to get blastn version: {e}")


def validate_file_exists(file_path: str, file_type: str = "file") -> Path:
    """
    Validate that a file exists and is readable.

    Args:
        file_path: Path to file
        file_type: Type of file for error message (e.g., "input FASTA")

    Returns:
        Path object for the validated file

    Raises:
        FileValidationError: If file doesn't exist or isn't readable
    """
    path = Path(file_path)

    if not path.exists():
        raise FileValidationError(f"{file_type} not found: {file_path}")

    if not path.is_file():
        raise FileValidationError(f"{file_type} is not a file: {file_path}")

    if not os.access(path, os.R_OK):
        raise FileValidationError(f"{file_type} is not readable: {file_path}")

    return path


def validate_output_path(file_path: str) -> Path:
    """
    Validate that output path is writable.

    Args:
        file_path: Path to output file

    Returns:
        Path object for the output file

    Raises:
        FileValidationError: If output directory doesn't exist or isn't writable
    """
    path = Path(file_path)

    # Check if parent directory exists and is writable
    parent = path.parent
    if not parent.exists():
        raise FileValidationError(f"Output directory does not exist: {parent}")

    if not os.access(parent, os.W_OK):
        raise FileValidationError(f"Output directory is not writable: {parent}")

    # If file exists, check if it's writable
    if path.exists() and not os.access(path, os.W_OK):
        raise FileValidationError(f"Output file exists but is not writable: {file_path}")

    return path


def validate_percentage(
    value: float, name: str, min_val: float = 0.0, max_val: float = 100.0
) -> float:
    """
    Validate that a value is a valid percentage.

    Args:
        value: Value to validate
        name: Name of parameter for error message
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        The validated value

    Raises:
        VotuDerepError: If value is out of range
    """
    if not min_val <= value <= max_val:
        raise VotuDerepError(f"{name} must be between {min_val} and {max_val}, got {value}")
    return value
