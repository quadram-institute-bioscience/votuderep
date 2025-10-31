"""
votuderep - A comprehensive toolkit for viral contig dereplication and quality filtering
==========================================================================================

**votuderep** is a command-line tool designed for processing viral metagenomics data,
with a focus on dereplicating viral Operational Taxonomic Units (vOTUs) and filtering
sequences based on quality metrics from CheckV.

Key Features
------------

- **Dereplication**: Cluster viral sequences by Average Nucleotide Identity (ANI) using BLAST
- **Quality Filtering**: Filter sequences based on CheckV quality assessment metrics
- **Database Management**: Download and manage geNomad and CheckV databases
- **Utility Tools**:
  - Generate sample tables from sequencing read directories
  - Split CoverM coverage tables by metric
  - Download training datasets for tutorials

Installation
------------

Install votuderep using pip:

    pip install votuderep

Or install from source:

    git clone https://github.com/yourusername/votuderep.git
    cd votuderep
    pip install -e .

Quick Start
-----------

### Dereplicate viral contigs

    votuderep derep -i viral_contigs.fasta -o dereplicated.fasta --min-ani 95 --min-tcov 85

### Filter by CheckV quality

    votuderep filter contigs.fasta checkv_output.tsv -o filtered.fasta --min-quality medium

### Download databases

    votuderep getdbs --outdir ./databases

### Generate sample table

    votuderep tabulate reads_directory/ -o samples.csv

Available Commands
------------------

Run `votuderep --help` to see all available commands:

- **derep**: Dereplicate vOTUs using BLAST and ANI clustering
- **filter**: Filter FASTA files using CheckV quality metrics
- **getdbs**: Download geNomad and CheckV databases
- **splitcoverm**: Split CoverM TSV by metric into separate files
- **tabulate**: Generate CSV file from a directory containing reads
- **trainingdata**: Download training datasets

Module Organization
-------------------

- `votuderep.commands`: CLI command implementations
- `votuderep.core`: Core business logic (BLAST, ANI calculation, filtering)
- `votuderep.utils`: Utility functions (I/O, validation, logging)

Requirements
------------

- Python >= 3.10
- BLAST+ toolkit (for dereplication)
- Dependencies: click, rich, pandas, pyfastx

Citation
--------

If you use votuderep in your research, please cite:

    Telatin, A. et al. (2024). votuderep: A tool for viral contig dereplication.

License
-------

MIT License - see LICENSE file for details

Version Information
-------------------
"""

__version__ = "0.6.0"
__author__ = "Andrea Telatin"
__license__ = "MIT"

__all__ = ["__version__", "__author__", "__license__"]
