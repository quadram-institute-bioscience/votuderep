# Quick Start Guide

This guide will walk you through the most common workflows with votuderep.

## Basic Workflow

The typical workflow for processing viral contigs involves:

1. **Download databases** (one-time setup)
2. **Filter** viral contigs by quality (using CheckV output)
3. **Dereplicate** to remove redundant sequences

## 1. Download Databases

First, download the required databases for viral annotation tools:

```bash
# Download all databases (geNomad, CheckV, PHROGs)
votuderep getdbs -o ./databases/

# Or download specific databases
votuderep getdbs -o ./databases/ --db genomad_1.9
votuderep getdbs -o ./databases/ --db checkv_1.5
```

!!! note
    This is a one-time setup. The databases can be reused for multiple analyses.

## 2. Filter Viral Contigs

After running CheckV on your viral contigs, filter them based on quality metrics:

```bash
# Basic filtering - keep sequences with minimum quality
votuderep filter viral_contigs.fasta checkv_output.tsv -o filtered.fasta

# High-quality sequences only
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --min-quality high -o high_quality.fasta

# Complete genomes with minimum length
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --complete --min-len 5000 -o complete_genomes.fasta
```

## 3. Dereplicate Sequences

Remove redundant sequences using BLAST-based ANI clustering:

```bash
# Basic dereplication (95% ANI, 85% coverage)
votuderep derep -i filtered.fasta -o dereplicated.fasta

# Custom parameters with more threads
votuderep derep -i filtered.fasta -o dereplicated.fasta \
  --min-ani 97 --min-tcov 90 -t 8
```

## Complete Example

Here's a complete workflow from start to finish:

```bash
# Step 1: Download databases (one-time)
votuderep getdbs -o ./databases/ --db checkv_1.5

# Step 2: Run CheckV on your viral contigs (external tool)
# checkv end_to_end viral_contigs.fasta checkv_out/ -d ./databases/checkv-db-v1.5

# Step 3: Filter based on CheckV quality
votuderep filter viral_contigs.fasta checkv_out/quality_summary.tsv \
  --min-quality medium \
  --min-completeness 50 \
  --min-len 3000 \
  -o filtered_contigs.fasta

# Step 4: Dereplicate the filtered sequences
votuderep derep -i filtered_contigs.fasta \
  -o final_vOTUs.fasta \
  --min-ani 95 \
  --min-tcov 85 \
  -t 8
```

## Working with Sequencing Reads

If you need to create a sample table for Nextflow pipelines:

```bash
# Generate CSV from paired-end reads directory
votuderep tabulate reads/ -o samples.csv

# With custom read tags
votuderep tabulate reads/ \
  --for-tag _1.fastq.gz \
  --rev-tag _2.fastq.gz \
  -o samples.csv
```

## Getting Help

Every command has detailed help available:

```bash
# General help
votuderep --help

# Command-specific help
votuderep derep --help
votuderep filter --help
votuderep getdbs --help
```

## Common Parameters

### ANI and Coverage Thresholds

For the `derep` command:

- `--min-ani`: Average Nucleotide Identity threshold (0-100)
    - Default: 95.0
    - Higher = stricter (fewer clusters)
    - Common values: 95-99
- `--min-tcov`: Minimum target coverage (0-100)
    - Default: 85.0
    - Percentage of the sequence that must be covered

### Quality Filtering

For the `filter` command:

- `--min-quality`: Minimum CheckV quality level
    - `low`: Includes all quality levels (default)
    - `medium`: Includes Medium, High, and Complete
    - `high`: Includes only High and Complete
- `--min-completeness`: Minimum genome completeness (0-100)
- `--max-contam`: Maximum contamination percentage

## Next Steps

- Explore individual [CLI Commands](cli/index.md) for detailed options
- Read the [API Reference](api.md) for programmatic usage
- Check out the training data: `votuderep trainingdata`
