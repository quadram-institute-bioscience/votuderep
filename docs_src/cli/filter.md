# votuderep filter

Filter viral contigs based on CheckV quality metrics.

## Overview

The `filter` command processes viral contigs using quality assessment results from CheckV. It allows you to select sequences based on multiple criteria including quality level, completeness, contamination, length, and more.

## Usage

```bash
votuderep filter [OPTIONS] FASTA CHECKV_OUT
```

### Required Arguments

- `FASTA` - Input FASTA file with viral contigs
- `CHECKV_OUT` - TSV output file from CheckV (quality_summary.tsv)

### Options

**Output:**
- `-o, --output FILE` - Output FASTA file (default: STDOUT)

**Length Filters:**
- `-m, --min-len INTEGER` - Minimum contig length
- `--max-len INTEGER` - Maximum contig length (0 = unlimited)

**Quality Filters:**
- `--min-quality [low|medium|high]` - Minimum quality level (default: low)
- `--complete` - Only keep complete genomes
- `--exclude-undetermined` - Exclude contigs with quality "Not-determined"

**Metrics Filters:**
- `-c, --min-completeness FLOAT` - Minimum completeness percentage
- `--max-contam FLOAT` - Maximum contamination percentage
- `--no-warnings` - Only keep contigs with no warnings

**Other:**
- `--provirus` - Only select proviruses

## Examples

### Basic Quality Filtering

Keep only sequences with at least "low" quality (default):

```bash
votuderep filter viral_contigs.fasta checkv_output.tsv -o filtered.fasta
```

### High-Quality Sequences

Keep only high-quality and complete sequences:

```bash
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --min-quality high \
  -o high_quality.fasta
```

### Complete Genomes Only

Select only complete viral genomes:

```bash
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --complete \
  -o complete_genomes.fasta
```

### Length Filtering

Filter by minimum and maximum length:

```bash
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --min-len 5000 \
  --max-len 200000 \
  -o size_filtered.fasta
```

### Complex Filtering

Combine multiple criteria:

```bash
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --min-quality medium \
  --min-completeness 80 \
  --max-contam 5 \
  --no-warnings \
  --min-len 3000 \
  --exclude-undetermined \
  -o high_confidence.fasta
```

### Provirus Selection

Select only proviruses:

```bash
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --provirus \
  -o proviruses.fasta
```

### Output to Stdout

Use in a pipeline:

```bash
votuderep filter viral_contigs.fasta checkv_output.tsv | \
  gzip > filtered.fasta.gz
```

## CheckV Quality Levels

CheckV assigns quality levels to viral contigs based on completeness and other metrics:

| Quality Level | Description | Typical Use |
|--------------|-------------|-------------|
| **Complete** | Complete circular genomes or genomes with DTRs/ITRs | Highest confidence analyses |
| **High-quality** | >90% completeness | Genome-level studies |
| **Medium-quality** | 50-90% completeness | Most comparative analyses |
| **Low-quality** | <50% completeness | Large-scale surveys |
| **Not-determined** | Quality could not be assessed | Usually excluded |

### Quality Filtering Behavior

The `--min-quality` option is **inclusive** and hierarchical:

- `--min-quality low`: Includes Low, Medium, High, and Complete
- `--min-quality medium`: Includes Medium, High, and Complete
- `--min-quality high`: Includes only High and Complete

!!! note
    "Not-determined" sequences are **included by default** unless you use `--exclude-undetermined`.

## Filter Categories

### Length Filters

- `--min-len`: Minimum contig length in base pairs
- `--max-len`: Maximum contig length (0 = unlimited)

Useful for:
- Removing very short fragments
- Focusing on typical viral genome sizes
- Excluding potential chimeras or misassemblies

### Quality Filters

- `--min-quality`: Minimum CheckV quality level (low/medium/high)
- `--complete`: Select only complete genomes
- `--exclude-undetermined`: Exclude sequences where quality is "Not-determined"

### Metrics Filters

- `--min-completeness`: Minimum completeness percentage (0-100)
- `--max-contam`: Maximum contamination percentage (0-100)
- `--no-warnings`: Only keep sequences with no CheckV warnings

### Provirus Filter

- `--provirus`: Select only proviruses (integrated viral sequences)

## Practical Filtering Strategies

### Conservative Approach

For high-confidence downstream analyses:

```bash
votuderep filter contigs.fasta checkv.tsv \
  --min-quality high \
  --min-completeness 90 \
  --max-contam 5 \
  --no-warnings \
  -o conservative.fasta
```

### Balanced Approach

For most comparative genomics studies:

```bash
votuderep filter contigs.fasta checkv.tsv \
  --min-quality medium \
  --min-completeness 50 \
  --min-len 5000 \
  -o balanced.fasta
```

### Permissive Approach

For exploratory or large-scale surveys:

```bash
votuderep filter contigs.fasta checkv.tsv \
  --min-quality low \
  --min-len 3000 \
  -o permissive.fasta
```

## Tips

!!! tip "Pre-filtering for Dereplication"
    It's recommended to filter sequences **before** running `derep` to:

    1. Reduce computational time
    2. Ensure dereplicated set contains only quality sequences
    3. Avoid clustering low-quality fragments with genuine sequences

!!! warning "CheckV Output Format"
    Make sure to provide the CheckV `quality_summary.tsv` file, not the contamination or completeness files. This file contains all the metrics needed for filtering.

!!! info "Combining with grep"
    For complex filtering needs, you can combine with standard Unix tools:
    ```bash
    votuderep filter contigs.fasta checkv.tsv --min-quality medium | \
      grep -A 1 "specific_pattern"
    ```

## See Also

- [derep](derep.md) - Dereplicate filtered sequences
- [CheckV Documentation](https://bitbucket.org/berkeleylab/checkv/) - Learn about CheckV metrics
- [Quick Start Guide](../quickstart.md) - Complete workflow examples
