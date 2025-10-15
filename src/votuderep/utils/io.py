"""I/O utilities for reading and writing FASTA files."""

import sys
from pathlib import Path
from typing import Iterator, Tuple, Optional

try:
    import pyfastx
except ImportError:
    pyfastx = None


def read_fasta(file_path: str) -> Iterator[Tuple[str, str]]:
    """
    Read sequences from a FASTA file using pyfastx.

    Args:
        file_path: Path to FASTA file

    Yields:
        Tuple of (sequence_id, sequence)

    Raises:
        ImportError: If pyfastx is not installed
        FileNotFoundError: If file doesn't exist
    """
    if pyfastx is None:
        raise ImportError(
            "pyfastx is required for reading FASTA files. " "Install it with: pip install pyfastx"
        )

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {file_path}")

    # Use pyfastx to read FASTA file
    for name, seq in pyfastx.Fastx(str(path)):
        yield name, seq


def write_fasta(
    sequences: Iterator[Tuple[str, str]], output_path: Optional[str] = None, line_width: int = 80
) -> None:
    """
    Write sequences to a FASTA file or stdout.

    Args:
        sequences: Iterator of (sequence_id, sequence) tuples
        output_path: Path to output file, or None for stdout
        line_width: Number of characters per line (0 for no wrapping)

    Raises:
        IOError: If writing fails
    """
    # Determine output handle
    if output_path is None or output_path == "-":
        handle = sys.stdout
        close_handle = False
    else:
        handle = open(output_path, "w")
        close_handle = True

    try:
        for seq_id, sequence in sequences:
            # Write header
            handle.write(f">{seq_id}\n")

            # Write sequence with optional line wrapping
            if line_width > 0:
                for i in range(0, len(sequence), line_width):
                    handle.write(sequence[i : i + line_width] + "\n")
            else:
                handle.write(sequence + "\n")

    finally:
        if close_handle:
            handle.close()


def count_sequences(file_path: str) -> int:
    """
    Count the number of sequences in a FASTA file.

    Args:
        file_path: Path to FASTA file

    Returns:
        Number of sequences

    Raises:
        ImportError: If pyfastx is not installed
        FileNotFoundError: If file doesn't exist
    """
    if pyfastx is None:
        raise ImportError(
            "pyfastx is required for reading FASTA files. " "Install it with: pip install pyfastx"
        )

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {file_path}")

    count = 0
    for _ in pyfastx.Fastx(str(path)):
        count += 1
    return count


def get_sequence_lengths(file_path: str) -> dict[str, int]:
    """
    Get lengths of all sequences in a FASTA file.

    Args:
        file_path: Path to FASTA file

    Returns:
        Dictionary mapping sequence IDs to their lengths

    Raises:
        ImportError: If pyfastx is not installed
        FileNotFoundError: If file doesn't exist
    """
    if pyfastx is None:
        raise ImportError(
            "pyfastx is required for reading FASTA files. " "Install it with: pip install pyfastx"
        )

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {file_path}")

    lengths = {}
    for name, seq in pyfastx.Fastx(str(path)):
        lengths[name] = len(seq)

    return lengths


def filter_sequences(
    file_path: str, sequence_ids: set[str], output_path: Optional[str] = None, exclude: bool = False
) -> int:
    """
    Filter sequences from a FASTA file by ID.

    Args:
        file_path: Path to input FASTA file
        sequence_ids: Set of sequence IDs to keep (or exclude)
        output_path: Path to output file, or None for stdout
        exclude: If True, exclude the given IDs instead of keeping them

    Returns:
        Number of sequences written

    Raises:
        ImportError: If pyfastx is not installed
        FileNotFoundError: If file doesn't exist
    """
    count = 0

    def filtered_sequences():
        nonlocal count
        for seq_id, seq in read_fasta(file_path):
            should_include = (seq_id in sequence_ids) != exclude
            if should_include:
                count += 1
                yield seq_id, seq

    write_fasta(filtered_sequences(), output_path)
    return count
