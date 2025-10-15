"""BLAST operations for vOTU dereplication."""

import subprocess

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

logger = get_logger(__name__)


def run_makeblastdb(input_fasta: str, output_db: str, dbtype: str = "nucl") -> None:
    """
    Create a BLAST database from a FASTA file.

    Args:
        input_fasta: Path to input FASTA file
        output_db: Path prefix for output database
        dbtype: Database type ('nucl' or 'prot')

    Raises:
        VotuDerepError: If makeblastdb fails
    """
    cmd = ["makeblastdb", "-in", input_fasta, "-dbtype", dbtype, "-out", output_db]

    logger.info(f"Creating BLAST database: {output_db}")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.debug(f"makeblastdb output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"makeblastdb failed: {e.stderr}")
        raise VotuDerepError(f"Failed to create BLAST database: {e.stderr}")


def run_blastn(
    query: str,
    database: str,
    output: str,
    threads: int = 2,
    max_target_seqs: int = 10000,
    evalue: float = 1e-3,
) -> None:
    """
    Run BLASTN for all-vs-all comparison.

    Args:
        query: Path to query FASTA file
        database: Path prefix to BLAST database
        output: Path to output file
        threads: Number of threads to use
        max_target_seqs: Maximum number of target sequences
        evalue: E-value threshold

    Raises:
        VotuDerepError: If blastn fails
    """
    cmd = [
        "blastn",
        "-query",
        query,
        "-db",
        database,
        "-out",
        output,
        "-outfmt",
        "6 std qlen slen",
        "-max_target_seqs",
        str(max_target_seqs),
        "-num_threads",
        str(threads),
        "-evalue",
        str(evalue),
    ]

    logger.info(f"Running BLASTN with {threads} threads")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            logger.debug(f"blastn output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"blastn failed: {e.stderr}")
        raise VotuDerepError(f"Failed to run BLASTN: {e.stderr}")

    logger.info(f"BLASTN results written to: {output}")
