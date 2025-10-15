"""Filtering sequences based on CheckV quality metrics."""

from typing import Set, Optional

import pandas as pd

from ..utils.logging import get_logger

logger = get_logger(__name__)


# Quality level hierarchy
QUALITY_LEVELS = {
    "Complete": 5,
    "High-quality": 4,
    "Medium-quality": 3,
    "Low-quality": 2,
    "Not-determined": 1,
}


def parse_quality_threshold(min_quality: str) -> int:
    """
    Parse minimum quality threshold.

    Args:
        min_quality: One of 'low', 'medium', 'high'

    Returns:
        Minimum quality level value

    Raises:
        ValueError: If min_quality is invalid
    """
    quality_map = {
        "low": 2,  # Low-quality, Medium-quality, High-quality, Complete
        "medium": 3,  # Medium-quality, High-quality, Complete
        "high": 4,  # High-quality, Complete
    }

    if min_quality not in quality_map:
        raise ValueError(
            f"Invalid min_quality: {min_quality}. "
            f"Must be one of: {', '.join(quality_map.keys())}"
        )

    return quality_map[min_quality]


def filter_by_checkv(
    checkv_file: str,
    min_len: int = 0,
    max_len: int = 0,
    provirus_only: bool = False,
    min_completeness: Optional[float] = None,
    max_contam: Optional[float] = None,
    no_warnings: bool = False,
    exclude_undetermined: bool = False,
    complete_only: bool = False,
    min_quality: str = "low",
) -> Set[str]:
    """
    Filter sequence IDs based on CheckV quality metrics.

    Args:
        checkv_file: Path to CheckV TSV output file
        min_len: Minimum contig length (0 = no minimum)
        max_len: Maximum contig length (0 = no maximum)
        provirus_only: Only keep proviruses (provirus == "Yes")
        min_completeness: Minimum completeness percentage
        max_contam: Maximum contamination percentage
        no_warnings: Only keep contigs with no warnings
        exclude_undetermined: Exclude contigs with checkv_quality == "Not-determined"
        complete_only: Only keep contigs with checkv_quality == "Complete"
        min_quality: Minimum quality level ('low', 'medium', 'high')

    Returns:
        Set of sequence IDs that pass all filters
    """
    logger.info(f"Loading CheckV results from: {checkv_file}")

    # Read CheckV file
    df = pd.read_csv(checkv_file, sep="\t")
    initial_count = len(df)
    logger.info(f"Loaded {initial_count} contigs from CheckV file")

    # Apply length filters
    if min_len > 0:
        before = len(df)
        df = df[df["contig_length"] >= min_len]
        logger.debug(f"Min length filter ({min_len}): {before} -> {len(df)}")

    if max_len > 0:
        before = len(df)
        df = df[df["contig_length"] <= max_len]
        logger.debug(f"Max length filter ({max_len}): {before} -> {len(df)}")

    # Provirus filter
    if provirus_only:
        before = len(df)
        df = df[df["provirus"] == "Yes"]
        logger.debug(f"Provirus filter: {before} -> {len(df)}")

    # Completeness filter
    if min_completeness is not None:
        before = len(df)
        # Handle NaN values - keep only rows with completeness >= threshold
        df = df[df["completeness"].notna() & (df["completeness"] >= min_completeness)]
        logger.debug(f"Min completeness filter ({min_completeness}%): {before} -> {len(df)}")

    # Contamination filter
    if max_contam is not None:
        before = len(df)
        # Handle NaN values - keep rows with contamination <= threshold or NaN
        df = df[df["contamination"].isna() | (df["contamination"] <= max_contam)]
        logger.debug(f"Max contamination filter ({max_contam}%): {before} -> {len(df)}")

    # Warnings filter
    if no_warnings:
        before = len(df)
        # Keep only rows where warnings is empty/NaN
        df = df[df["warnings"].isna() | (df["warnings"] == "")]
        logger.debug(f"No warnings filter: {before} -> {len(df)}")

    # Complete only filter
    if complete_only:
        before = len(df)
        df = df[df["checkv_quality"] == "Complete"]
        logger.debug(f"Complete only filter: {before} -> {len(df)}")
    else:
        # Quality level filter
        min_quality_level = parse_quality_threshold(min_quality)

        # Map quality to numeric values
        df["quality_level"] = df["checkv_quality"].map(QUALITY_LEVELS)

        # Apply quality filter
        before = len(df)
        df = df[df["quality_level"] >= min_quality_level]
        logger.debug(f"Min quality filter ({min_quality}): {before} -> {len(df)}")

        # Exclude undetermined if requested
        if exclude_undetermined:
            before = len(df)
            df = df[df["checkv_quality"] != "Not-determined"]
            logger.debug(f"Exclude undetermined filter: {before} -> {len(df)}")

    final_count = len(df)
    logger.info(
        f"Filtering complete: {initial_count} -> {final_count} contigs ({final_count/initial_count*100:.1f}%)"
    )

    # Return set of contig IDs
    return set(df["contig_id"].tolist())
