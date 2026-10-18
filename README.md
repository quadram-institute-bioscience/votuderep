# votuderep

[![Test](https://github.com/quadram-institute-bioscience/votuderep/actions/workflows/test.yml/badge.svg)](https://github.com/quadram-institute-bioscience/votuderep/actions/workflows/test.yml)
![PyPI - Version](https://img.shields.io/pypi/v/votuderep)
![PyPI - Downloads](https://img.shields.io/pypi/dm/votuderep)
![Conda Version](https://img.shields.io/conda/vn/bioconda/votuderep)
![Conda Downloads](https://img.shields.io/conda/dn/bioconda/votuderep)


![Logo](https://github.com/quadram-institute-bioscience/votuderep/raw/main/votuderep.png)

A Python CLI tool for dereplicating and filtering viral contigs (vOTUs - viral Operational Taxonomic Units)
using the CheckV method.

## Commands

| Command | Description |
|---------|-------------|
| `derep` | Remove redundant viral sequences using BLAST-based ANI clustering |
| `filter` | Filter viral contigs based on quality, completeness, and other metrics from CheckV TSV output |
| `brbh` | Find Best Reciprocal Best Hits between two nucleotide FASTA files |
| `tabulate` | Generate CSV tables from paired-end sequencing read directories (for Nextflow) |
| `trainingdata` | Fetch viral assembly datasets for training purposes |
| `getdbs` | Download Genomad and CheckV databases |
| `splitcoverm` | Split a CoverM TSV by metric into separate TSVs, one per metric |

## Requirements

- Python >= 3.10
- BLAST+ toolkit (`blastn` and `makeblastdb` in PATH)

## Installation

```bash
# From PyPI
pip install votuderep

# From conda
conda install -c bioconda votuderep

# From source
pip install -e .
```

## Documentation

Full documentation including all command options and examples is available in [`docs_src/`](docs_src/) or at the project site.

```bash
votuderep --help
votuderep <command> --help
```

## License

MIT License - See LICENSE file for details

## Authors

Andrea Telatin & QIB Core Bioinformatics

©️ Quadram Institute Bioscience 2025
