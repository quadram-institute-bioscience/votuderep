# API Reference

This page provides detailed API documentation for the votuderep Python package. You can use these modules programmatically in your own Python scripts.

## Package Information

::: votuderep
    options:
      show_root_heading: true
      show_source: false
      members:
        - __version__

## Core Modules

### Dereplication

The dereplication module handles ANI-based clustering of viral sequences.

::: votuderep.core.dereplication
    options:
      show_root_heading: true
      show_source: true
      members_order: source

### BLAST Operations

The BLAST module provides utilities for running and parsing BLAST results.

::: votuderep.core.blast
    options:
      show_root_heading: true
      show_source: true
      members_order: source

### Filtering

The filtering module handles quality-based filtering using CheckV metrics.

::: votuderep.core.filtering
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Utility Modules

### I/O Operations

File input/output utilities for reading and writing sequences.

::: votuderep.utils.io
    options:
      show_root_heading: true
      show_source: true
      members_order: source

### Logging

Logging configuration and utilities.

::: votuderep.utils.logging
    options:
      show_root_heading: true
      show_source: true
      members_order: source

### Validators

Input validation utilities.

::: votuderep.utils.validators
    options:
      show_root_heading: true
      show_source: true
      members_order: source

## Command Modules

### Derep Command

::: votuderep.commands.derep
    options:
      show_root_heading: true
      show_source: false
      members:
        - derep

### Filter Command

::: votuderep.commands.filter
    options:
      show_root_heading: true
      show_source: false
      members:
        - filter

### GetDBs Command

::: votuderep.commands.getdbs
    options:
      show_root_heading: true
      show_source: false
      members:
        - getdbs

### Tabulate Command

::: votuderep.commands.tabulate
    options:
      show_root_heading: true
      show_source: false
      members:
        - tabulate

### TrainingData Command

::: votuderep.commands.trainingdata
    options:
      show_root_heading: true
      show_source: false
      members:
        - trainingdata

### SplitCoverM Command

::: votuderep.commands.splitcoverm
    options:
      show_root_heading: true
      show_source: false
      members:
        - splitcoverm

## Programmatic Usage

You can use votuderep functionality in your own Python scripts:

### Example: Dereplication

```python
from votuderep.core.dereplication import dereplicate_sequences
from votuderep.core.blast import run_blast

# Read your sequences
sequences = {...}  # Your sequence dictionary

# Run BLAST comparison
blast_results = run_blast(
    sequences,
    threads=4,
    min_identity=95.0
)

# Perform clustering
representatives = dereplicate_sequences(
    sequences,
    blast_results,
    min_ani=95.0,
    min_coverage=85.0
)
```

### Example: Filtering

```python
from votuderep.core.filtering import filter_by_checkv
import pandas as pd

# Load CheckV results
checkv_df = pd.read_csv("checkv_output.tsv", sep="\t")

# Filter sequences
filtered_ids = filter_by_checkv(
    checkv_df,
    min_quality="medium",
    min_completeness=50.0,
    min_length=5000
)

# Use filtered IDs to select sequences
```

### Example: I/O Operations

```python
from votuderep.utils.io import read_fasta, write_fasta

# Read sequences
sequences = read_fasta("input.fasta")

# Process sequences
# ... your processing code ...

# Write results
write_fasta(filtered_sequences, "output.fasta")
```

## Type Hints

All modules include type hints for better IDE support and type checking:

```python
from typing import Dict, List, Tuple
from votuderep.core.dereplication import dereplicate_sequences

def my_function(sequences: Dict[str, str]) -> List[str]:
    """My custom function using votuderep."""
    # Type hints provide autocomplete and error checking
    representatives = dereplicate_sequences(sequences, ...)
    return list(representatives.keys())
```

## Error Handling

The package defines custom exceptions for better error handling:

```python
from votuderep.utils.validators import ValidationError

try:
    # Your code here
    process_sequences(input_file)
except ValidationError as e:
    print(f"Validation failed: {e}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

## See Also

- [CLI Commands](cli/index.md) - Command-line interface documentation
- [Quick Start Guide](quickstart.md) - Getting started with votuderep
- [GitHub Repository](https://github.com/quadram-institute-bioscience/votuderep) - Source code
