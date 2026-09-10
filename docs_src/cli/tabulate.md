# votuderep tabulate

Generate CSV tables from paired-end sequencing read directories.

## Overview

The `tabulate` command scans a directory containing paired-end sequencing reads and generates a structured CSV table. This is particularly useful for creating sample sheets for workflow managers like Nextflow, Snakemake, or custom scripts.

## Usage

```bash
votuderep tabulate [OPTIONS] INPUT_DIR
```

### Required Arguments

- `INPUT_DIR` - Directory containing sequencing read files

### Options

- `-o, --output FILE` - Output CSV file (default: STDOUT)
- `-d, --delimiter TEXT` - Field separator (default: ,)
- `-1, --for-tag TEXT` - Identifier for forward reads (default: _R1)
- `-2, --rev-tag TEXT` - Identifier for reverse reads (default: _R2)
- `-s, --strip TEXT` - Remove this string from sample names (can be used multiple times)
- `-e, --extension TEXT` - Only process files ending with this extension
- `-a, --absolute` - Use absolute paths in output

## Examples

### Basic Usage

Generate a CSV table from a reads directory:

```bash
votuderep tabulate reads/ -o samples.csv
```

**Input directory structure:**
```
reads/
├── sample1_R1.fastq.gz
├── sample1_R2.fastq.gz
├── sample2_R1.fastq.gz
└── sample2_R2.fastq.gz
```

**Output CSV:**
```csv
sample,R1,R2
sample1,reads/sample1_R1.fastq.gz,reads/sample1_R2.fastq.gz
sample2,reads/sample2_R1.fastq.gz,reads/sample2_R2.fastq.gz
```

### Custom Read Tags

If your files use different naming conventions:

```bash
votuderep tabulate reads/ \
  --for-tag _1.fq.gz \
  --rev-tag _2.fq.gz \
  -o samples.csv
```

This will match:
- `sample_1.fq.gz` (forward)
- `sample_2.fq.gz` (reverse)

### Filter by Extension

Process only files with specific extension:

```bash
votuderep tabulate reads/ \
  --extension .fastq.gz \
  -o samples.csv
```

### Absolute Paths

Use absolute paths in the output (useful for workflow managers):

```bash
votuderep tabulate reads/ \
  --absolute \
  -o samples.csv
```

**Output with absolute paths:**
```csv
sample,R1,R2
sample1,/full/path/to/reads/sample1_R1.fastq.gz,/full/path/to/reads/sample1_R2.fastq.gz
```

### Strip Patterns from Sample Names

Remove unwanted patterns from sample names:

```bash
votuderep tabulate reads/ \
  --strip "Sample_" \
  --strip ".filtered" \
  -o samples.csv
```

**Example:**
- Input: `Sample_001.filtered_R1.fastq.gz`
- Output sample name: `001`

Multiple `--strip` options are processed in order.

### Tab-Delimited Output

Use tabs instead of commas:

```bash
votuderep tabulate reads/ \
  --delimiter $'\t' \
  -o samples.tsv
```

### Output to Stdout

For piping to other commands:

```bash
votuderep tabulate reads/ | head -n 5
```

## Read Pair Detection

The command automatically pairs forward and reverse reads based on the tags:

1. **Scans directory** for files matching the extension filter (if specified)
2. **Identifies forward reads** containing the forward tag (default: `_R1`)
3. **Finds corresponding reverse reads** by replacing forward tag with reverse tag (default: `_R2`)
4. **Extracts sample name** by removing the forward tag and extension
5. **Applies strip patterns** to clean up sample names

### Naming Requirements

For successful pairing:

- Forward and reverse files must have **identical names** except for the R1/R2 tag
- Tags must be **unique** in the filename
- Both files in a pair must **exist**

!!! warning "Unpaired Reads"
    If a forward read file is found without a corresponding reverse read, that sample will be skipped with a warning message.

## Use Cases

### Nextflow Sample Sheet

Create a sample sheet for Nextflow pipelines:

```bash
votuderep tabulate reads/ \
  --absolute \
  --strip "Sample_" \
  -o samplesheet.csv
```

**Use in Nextflow:**
```groovy
Channel
    .fromPath('samplesheet.csv')
    .splitCsv(header: true)
    .map { row -> tuple(row.sample, file(row.R1), file(row.R2)) }
    .set { samples_ch }
```

### Snakemake Configuration

Generate a sample table for Snakemake:

```bash
votuderep tabulate reads/ \
  --delimiter $'\t' \
  -o config/samples.tsv
```

### Quality Control Verification

List all paired reads for verification:

```bash
votuderep tabulate reads/ | column -t -s,
```

### Subset Selection

Extract specific samples:

```bash
votuderep tabulate reads/ | grep "control\|treatment"
```

## Advanced Examples

### Complex Naming Convention

For files like `ProjectX_Sample001_Lane1_R1_001.fastq.gz`:

```bash
votuderep tabulate reads/ \
  --for-tag _R1_001 \
  --rev-tag _R2_001 \
  --strip "ProjectX_" \
  --strip "_Lane1" \
  -o samples.csv
```

**Result:**
- Sample name: `Sample001`
- Matched pairs properly identified

### Multiple Read Directories

Combine reads from multiple directories:

```bash
# Create separate CSVs
votuderep tabulate batch1/ -o batch1.csv
votuderep tabulate batch2/ -o batch2.csv

# Combine (skip first header)
cat batch1.csv > all_samples.csv
tail -n +2 batch2.csv >> all_samples.csv
```

### Validation Script

Generate table and validate pairs exist:

```bash
votuderep tabulate reads/ -o samples.csv

# Verify all files exist
tail -n +2 samples.csv | cut -d',' -f2,3 | tr ',' '\n' | while read file; do
  [ -f "$file" ] || echo "Missing: $file"
done
```

## Output Format

The generated CSV always has three columns:

| Column | Description | Example |
|--------|-------------|---------|
| `sample` | Sample identifier (basename without R1/R2 and extension) | `sample1` |
| `R1` | Path to forward read file | `reads/sample1_R1.fastq.gz` |
| `R2` | Path to reverse read file | `reads/sample1_R2.fastq.gz` |

## Tips

!!! tip "Testing Patterns"
    Before generating the final table, test your strip patterns:
    ```bash
    votuderep tabulate reads/ --strip "pattern" | head -n 3
    ```

!!! tip "Duplicate Sample Names"
    If multiple file pairs resolve to the same sample name after stripping, only the last one will be included. Use `--verbose` to see warnings.

!!! tip "Relative vs Absolute Paths"
    - Use **relative paths** (default) for portable sample sheets
    - Use **absolute paths** (`--absolute`) for workflow managers or when reads are in different locations

## Common Issues

### No Pairs Found

If no pairs are detected:

1. Check your read tags match the files: `ls reads/*R1*`
2. Try without extension filter: remove `--extension`
3. Use verbose mode to see what's being processed: `-v`

### Wrong Sample Names

If sample names aren't what you expect:

1. Check what's being detected: `votuderep tabulate reads/ | cat`
2. Add strip patterns to remove unwanted parts
3. Adjust the for-tag and rev-tag if needed

### Files in Subdirectories

The command only searches the specified directory, not subdirectories. To process subdirectories:

```bash
# Process each subdirectory separately
for dir in reads/*/; do
  votuderep tabulate "$dir" >> all_samples.csv
done
```

## See Also

- [Quick Start Guide](../quickstart.md) - Using tabulate in workflows
- [trainingdata](trainingdata.md) - Download example sequencing data
