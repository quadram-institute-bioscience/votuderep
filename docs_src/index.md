# votuderep

[![Test](https://github.com/quadram-institute-bioscience/votuderep/actions/workflows/test.yml/badge.svg)](https://github.com/quadram-institute-bioscience/votuderep/actions/workflows/test.yml)
![PyPI - Version](https://img.shields.io/pypi/v/votuderep)
![PyPI - Downloads](https://img.shields.io/pypi/dm/votuderep)
![Conda Version](https://img.shields.io/conda/vn/bioconda/votuderep)
![Conda Downloads](https://img.shields.io/conda/dn/bioconda/votuderep)

![Logo](https://github.com/quadram-institute-bioscience/votuderep/raw/main/votuderep.png)

A Python CLI tool for dereplicating and filtering viral contigs (vOTUs - viral Operational Taxonomic Units) using the CheckV method.

## Overview

**votuderep** is a small toolkit developed for the [EBAME](https://maignienlab.gitlab.io/ebame/) workshop with subcommands for working with viral sequences:

- **[derep](cli/derep.md)**: Remove redundant viral sequences using BLAST-based ANI clustering
- **[filter](cli/filter.md)**: Filter viral contigs based on quality, completeness, and other metrics from CheckV tsv output
- **[getdbs](cli/getdbs.md)**: Download geNomad, CheckV, and PHROGs databases
- **[tabulate](cli/tabulate.md)**: Generate CSV tables from paired-end sequencing read directories (for nextflow)
- **[trainingdata](cli/trainingdata.md)**: Fetch viral assembly datasets for training purposes
- **[splitcoverm](cli/splitcoverm.md)**: Split a CoverM TSV by metric into separate TSVs, one per metric

## Requirements

- Python >= 3.10
- BLAST+ toolkit (specifically `blastn` and `makeblastdb`)

## Quick Links

- [Installation Guide](installation.md)
- [Quick Start Tutorial](quickstart.md)
- [CLI Commands Overview](cli/index.md)
- [API Reference](api.md)

## Global Options

All commands support the following global options:

- `-v, --verbose`: Enable verbose logging
- `-h, --help`: Show help message (also `--help`)
- `--version`: Show version and exit

## License

MIT License - See LICENSE file for details

## Authors

**Andrea Telatin** & QIB Core Bioinformatics

©️ Quadram Institute Bioscience 2025
