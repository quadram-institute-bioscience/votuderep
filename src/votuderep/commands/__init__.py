"""
Command modules for votuderep CLI
==================================

This package contains all CLI command implementations for votuderep.
Each module implements a specific command that can be invoked from the command line.

Available command modules:

- `votuderep.commands.derep`: Dereplicate vOTUs using BLAST and ANI clustering
- `votuderep.commands.filter`: Filter FASTA files using CheckV quality metrics
- `votuderep.commands.getdbs`: Download geNomad and CheckV databases
- `votuderep.commands.splitcoverm`: Split CoverM TSV by metric into separate files
- `votuderep.commands.tabulate`: Generate CSV file from a directory containing reads
- `votuderep.commands.trainingdata`: Download training datasets from the internet
"""

# Import command modules for documentation
from . import derep, filter, getdbs, splitcoverm, tabulate, trainingdata

# Import command functions for backward compatibility
from .derep import derep as derep_cmd
from .filter import filter_cmd

__all__ = [
    # Modules (for pdoc)
    "derep",
    "filter",
    "getdbs",
    "splitcoverm",
    "tabulate",
    "trainingdata",
    # Command functions (for CLI)
    "derep_cmd",
    "filter_cmd",
]
