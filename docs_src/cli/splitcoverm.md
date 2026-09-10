# votuderep splitcoverm

Split CoverM TSV output by metric into separate files for easier downstream analysis.

## Overview

The `splitcoverm` command processes CoverM output tables containing multiple coverage metrics across samples and splits them into individual TSV files—one per metric. This simplifies downstream analysis by providing separate files for each metric (coverage, mean, variance, etc.).

CoverM outputs tables where each sample has multiple metric columns. This command reorganizes the data so each metric gets its own file with samples as columns.

## Usage

```bash
votuderep splitcoverm [OPTIONS]
```

### Required Options

- `-i, --input FILE` - Input CoverM TSV (optionally gzipped: .gz)
- `-o, --output-basename TEXT` - Output basename/prefix for generated files

## Examples

### Basic Usage

Split a CoverM output file:

```bash
votuderep splitcoverm -i coverage.tsv -o output/sample
```

**Input file (`coverage.tsv`):**
```tsv
Contig              Sample1 Mean  Sample1 Variance  Sample2 Mean  Sample2 Variance
contig_001          45.2          12.3             38.7          10.1
contig_002          67.8          15.9             72.3          14.2
```

**Output files:**
- `output/sample_Mean.tsv`
- `output/sample_Variance.tsv`

**Output file (`output/sample_Mean.tsv`):**
```tsv
Contig      Sample1  Sample2
contig_001  45.2     38.7
contig_002  67.8     72.3
```

### Gzipped Input

The command automatically handles gzipped input:

```bash
votuderep splitcoverm -i coverage.tsv.gz -o results/cov
```

### Custom Output Path

Specify a full path including directory and prefix:

```bash
votuderep splitcoverm \
  -i coverage.tsv \
  -o /path/to/results/experiment1_coverage
```

This creates files like:
- `/path/to/results/experiment1_coverage_Mean.tsv`
- `/path/to/results/experiment1_coverage_Variance.tsv`

### With Verbose Output

See detailed processing information:

```bash
votuderep -v splitcoverm -i coverage.tsv -o output/prefix
```

## CoverM Metrics

CoverM can calculate various coverage metrics. Common metrics you'll see in split files:

| Metric | Description | Typical Use |
|--------|-------------|-------------|
| **Mean** | Average coverage depth | General abundance estimation |
| **Variance** | Coverage variance | Quality/uniformity assessment |
| **Covered Bases** | Number of bases covered | Breadth of coverage |
| **Covered Fraction** | Proportion of sequence covered | Coverage completeness |
| **RPM** | Reads Per Million | Normalized abundance |
| **RPKM** | Reads Per Kilobase Million | Length-normalized abundance |
| **TPM** | Transcripts Per Million | Relative abundance |
| **Trimmed Mean** | Mean after outlier removal | Robust abundance estimate |

## Input Format Requirements

The command expects CoverM's standard TSV format:

1. **First column:** Contig/sequence identifiers
2. **Remaining columns:** Sample-metric pairs in format: `<sample_name> <metric_name>`
3. **Header row:** Column names (required)
4. **Tab-delimited:** Fields separated by tabs

**Example header:**
```
Contig    Sample1 Mean    Sample1 Variance    Sample2 Mean    Sample2 Variance
```

## Output Format

Each generated file:

- **Filename:** `<basename>_<metric>.tsv`
- **First column:** Contig identifiers (from input)
- **Other columns:** One per sample (values for that metric)
- **Tab-delimited:** Standard TSV format

## Use Cases

### Differential Abundance Analysis

Split metrics for statistical analysis:

```bash
# Split coverage file
votuderep splitcoverm -i coverage.tsv -o analysis/cov

# Use mean coverage for differential abundance
Rscript differential_abundance.R analysis/cov_Mean.tsv
```

### Heatmap Visualization

Create heatmaps for specific metrics:

```bash
# Split file
votuderep splitcoverm -i coverage.tsv -o viz/data

# Generate heatmap from mean coverage
python plot_heatmap.py viz/data_Mean.tsv -o mean_coverage_heatmap.png
```

### Metric Comparison

Compare different metrics for quality control:

```bash
votuderep splitcoverm -i coverage.tsv -o qc/metrics

# Compare mean vs trimmed mean
Rscript compare_metrics.R \
  qc/metrics_Mean.tsv \
  qc/metrics_TrimmedMean.tsv
```

### Integration with R/Python

Simplify data loading in analysis scripts:

**R example:**
```R
# After splitting
mean_cov <- read.table("output/sample_Mean.tsv", header=TRUE, sep="\t")
variance <- read.table("output/sample_Variance.tsv", header=TRUE, sep="\t")

# Proceed with analysis
```

**Python example:**
```python
import pandas as pd

# After splitting
mean_df = pd.read_csv("output/sample_Mean.tsv", sep="\t")
variance_df = pd.read_csv("output/sample_Variance.tsv", sep="\t")

# Proceed with analysis
```

### Filtering and Selection

Extract only the metrics you need:

```bash
# Split all metrics
votuderep splitcoverm -i coverage.tsv -o all/data

# Use only mean coverage for downstream analysis
cp all/data_Mean.tsv analysis/abundance.tsv
```

## Advanced Examples

### Batch Processing

Process multiple CoverM outputs:

```bash
for file in coverm_outputs/*.tsv; do
  basename=$(basename "$file" .tsv)
  votuderep splitcoverm -i "$file" -o "split_metrics/$basename"
done
```

### Pipeline Integration

Use in a pipeline with CoverM:

```bash
# Run CoverM
coverm contig \
  -r reference.fasta \
  -b *.bam \
  -m mean variance covered_fraction \
  > coverage.tsv

# Split metrics
votuderep splitcoverm -i coverage.tsv -o results/coverage

# Continue with analysis
Rscript analyze_abundance.R results/coverage_Mean.tsv
```

### Compress Output

Create compressed output files:

```bash
# Split files
votuderep splitcoverm -i coverage.tsv -o results/cov

# Compress individually
gzip results/cov_*.tsv

# Or compress all at once
find results/ -name "cov_*.tsv" -exec gzip {} \;
```

## Output Organization

For better organization, use descriptive basenames:

```bash
# Good: descriptive basename
votuderep splitcoverm \
  -i coverage.tsv \
  -o results/projectX_viral_contigs_coverage

# Creates:
# results/projectX_viral_contigs_coverage_Mean.tsv
# results/projectX_viral_contigs_coverage_Variance.tsv
```

## Performance Considerations

- **Large files:** Processing time scales with file size
- **Memory:** The entire table is loaded into memory
- **Gzipped input:** Slightly slower but saves disk space
- **Output:** All output files written simultaneously

For very large files:
```bash
# Use verbose mode to monitor progress
votuderep -v splitcoverm -i large_file.tsv.gz -o output/prefix

# Consider working on a fast filesystem (SSD)
```

## Troubleshooting

### Format Errors

If you get a format error:

1. **Check input format:** Ensure it's CoverM output TSV
2. **Verify tab-delimited:** Some tools output space-delimited
3. **Check header:** Must have proper column names
4. **Inspect file:**
   ```bash
   head -n 2 coverage.tsv | cat -A
   ```

### No Output Files

If no files are generated:

1. **Check input exists:** `ls -lh coverage.tsv`
2. **Verify output directory exists or is writable**
3. **Use verbose mode:** `votuderep -v splitcoverm ...`
4. **Check for error messages**

### Unexpected Metric Names

If metric names in output filenames look wrong:

- Check the CoverM command that generated the input
- The metric names come directly from CoverM column headers
- Spaces in metric names will be preserved in filenames

### Memory Issues

For very large files:

```bash
# Check file size first
ls -lh coverage.tsv

# If too large, consider splitting the input first
split -l 100000 coverage.tsv coverage_part_

# Process each part
for part in coverage_part_*; do
  votuderep splitcoverm -i "$part" -o "results/${part}"
done
```

## Tips

!!! tip "Check CoverM Output First"
    Before splitting, inspect your CoverM output to understand what metrics are included:
    ```bash
    head -n 1 coverage.tsv | tr '\t' '\n'
    ```

!!! tip "Consistent Naming"
    Use consistent basename patterns for easier file management:
    ```bash
    votuderep splitcoverm -i sample1.tsv -o split/sample1_cov
    votuderep splitcoverm -i sample2.tsv -o split/sample2_cov
    ```

!!! tip "Automate with Make"
    For reproducible workflows, use Make:
    ```makefile
    split/%.tsv: coverm/%.tsv
        votuderep splitcoverm -i $< -o split/$(basename $<)
    ```

## Integration with CoverM

CoverM is a tool for calculating coverage metrics from BAM files. Typical workflow:

```bash
# 1. Map reads to contigs (using tools like BWA, Bowtie2)
bwa mem ref.fasta sample_R1.fq sample_R2.fq | samtools sort -o sample.bam

# 2. Run CoverM to calculate metrics
coverm contig \
  -b sample1.bam sample2.bam \
  -m mean variance rpkm \
  > coverage.tsv

# 3. Split by metric
votuderep splitcoverm -i coverage.tsv -o analysis/coverage

# 4. Analyze individual metrics
Rscript analyze.R analysis/coverage_Mean.tsv
```

## See Also

- [CoverM Documentation](https://github.com/wwood/CoverM) - Learn about CoverM
- [Quick Start Guide](../quickstart.md) - Complete workflow examples
- [derep](derep.md) - Dereplicate sequences after abundance analysis
