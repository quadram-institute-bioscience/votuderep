"""
Core business logic for votuderep
==================================

This package contains the core algorithms and business logic for votuderep,
including BLAST operations, ANI calculation, clustering, and quality filtering.

Available core modules:

- `votuderep.core.blast`: BLAST database creation and sequence comparison
- `votuderep.core.dereplication`: ANI calculation and sequence clustering algorithms
- `votuderep.core.filtering`: CheckV-based quality filtering logic
"""

# Import modules for documentation
from . import blast, dereplication, filtering

# Import functions for API
from .blast import run_makeblastdb, run_blastn
from .dereplication import calculate_ani, cluster_by_ani, dereplicate_sequences
from .filtering import filter_by_checkv

__all__ = [
    # Modules (for pdoc)
    "blast",
    "dereplication",
    "filtering",
    # Functions (for API)
    "run_makeblastdb",
    "run_blastn",
    "calculate_ani",
    "cluster_by_ani",
    "dereplicate_sequences",
    "filter_by_checkv",
]
