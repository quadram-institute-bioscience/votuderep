# CLI Commands Overview

votuderep provides a comprehensive set of command-line tools for working with viral sequences (vOTUs).

## Available Commands

### Core Commands

#### [derep](derep.md)
Remove redundant viral sequences using BLAST-based ANI clustering. This is the main dereplication command that uses average nucleotide identity (ANI) and coverage thresholds to identify and remove similar sequences.

**Quick Example:**
```bash
votuderep derep -i input.fasta -o dereplicated.fasta --min-ani 95 --min-tcov 85
```

#### [filter](filter.md)
Filter viral contigs based on CheckV quality metrics. Use this command after running CheckV to select sequences based on quality, completeness, contamination, and other criteria.

**Quick Example:**
```bash
votuderep filter contigs.fasta checkv_output.tsv --min-quality high -o filtered.fasta
```

### Database Management

#### [getdbs](getdbs.md)
Download geNomad, CheckV, and PHROGs databases. This command simplifies database management by automatically downloading and setting up the required reference databases.

**Quick Example:**
```bash
votuderep getdbs -o ./databases/ --db all
```

### Utility Commands

#### [tabulate](tabulate.md)
Generate CSV tables from paired-end sequencing read directories. Useful for creating sample sheets for workflow managers like Nextflow.

**Quick Example:**
```bash
votuderep tabulate reads/ -o samples.csv
```

#### [trainingdata](trainingdata.md)
Download viral assembly and sequencing read datasets for training and testing purposes. Includes datasets from the EBAME workshop.

**Quick Example:**
```bash
votuderep trainingdata -o ./ebame-virome/
```

#### [splitcoverm](splitcoverm.md)
Split CoverM TSV output by metric into separate files. Each metric (coverage, mean, etc.) gets its own TSV file for easier downstream analysis.

**Quick Example:**
```bash
votuderep splitcoverm -i coverage.tsv -o output/prefix
```

## Global Options

All commands support these global options:

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message and exit |
| `--version` | Show program version and exit |
| `-v, --verbose` | Enable verbose logging output |

## Command Structure

All votuderep commands follow this general structure:

```bash
votuderep [GLOBAL_OPTIONS] <command> [COMMAND_OPTIONS] [ARGUMENTS]
```

**Example:**
```bash
votuderep -v derep -i input.fasta -o output.fasta --min-ani 97 -t 8
         │    │                                               │
         │    └─ command                                      └─ command options
         └─ global option
```

## Getting Help

Get detailed help for any command:

```bash
# General help
votuderep --help

# Command-specific help
votuderep derep --help
votuderep filter --help
```

## Common Workflows

### Basic Viral Contig Processing

1. **Filter quality sequences:**
   ```bash
   votuderep filter contigs.fasta checkv_out/quality_summary.tsv \
     --min-quality medium -o filtered.fasta
   ```

2. **Dereplicate:**
   ```bash
   votuderep derep -i filtered.fasta -o final_vOTUs.fasta
   ```

### Database Setup

```bash
# Download all databases
votuderep getdbs -o ./databases/

# Or download specific databases
votuderep getdbs -o ./databases/ --db checkv_1.5
votuderep getdbs -o ./databases/ --db genomad_1.9
```

### Preparing Sample Sheets

```bash
# Create sample sheet from reads directory
votuderep tabulate reads/ -o samples.csv --for-tag _R1 --rev-tag _R2
```

## Next Steps

Click on any command above to see its detailed documentation with all available options and usage examples.
