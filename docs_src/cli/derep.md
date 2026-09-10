# votuderep derep

Remove redundant viral sequences using BLAST-based ANI (Average Nucleotide Identity) clustering.

## Overview

The `derep` command performs dereplication of viral sequences by:

1. Running all-vs-all BLAST comparison
2. Calculating ANI and alignment coverage for each pair
3. Clustering sequences based on ANI and coverage thresholds
4. Selecting representative sequences from each cluster

This is useful for reducing redundancy in viral contig datasets while maintaining diversity.

## Usage

```bash
votuderep derep [OPTIONS]
```

### Required Options

- `-i, --input PATH` - Input FASTA file containing vOTUs

### Options

- `-o, --output PATH` - Output FASTA file with dereplicated vOTUs (default: dereplicated_vOTUs.fasta)
- `-t, --threads INTEGER` - Number of threads for BLAST (default: 2)
- `--tmp TEXT` - Directory for temporary files (default: $TEMP or /tmp or ./)
- `--min-ani FLOAT` - Minimum ANI to consider two vOTUs as the same (default: 95.0)
- `--min-tcov FLOAT` - Minimum target coverage to consider two vOTUs as the same (default: 85.0)
- `--keep` - Keep the temporary directory after completion

## Examples

### Basic Dereplication

Use default thresholds (95% ANI, 85% coverage):

```bash
votuderep derep -i viral_contigs.fasta -o dereplicated.fasta
```

### Custom Parameters

Adjust ANI and coverage thresholds:

```bash
votuderep derep -i viral_contigs.fasta -o dereplicated.fasta \
  --min-ani 97 \
  --min-tcov 90 \
  -t 8
```

### Keep Intermediate Files

Useful for debugging or inspecting BLAST results:

```bash
votuderep derep -i viral_contigs.fasta -o dereplicated.fasta \
  --keep \
  --tmp ./temp_derep
```

This will preserve:
- BLAST database files
- BLAST output
- Intermediate clustering files

### Large Datasets

For large datasets, increase threads and use a dedicated temporary directory:

```bash
votuderep derep -i large_dataset.fasta -o dereplicated.fasta \
  --min-ani 95 \
  --min-tcov 85 \
  -t 16 \
  --tmp /scratch/temp_blast
```

## Parameters Explained

### ANI Threshold (`--min-ani`)

Average Nucleotide Identity measures sequence similarity:

- **95%** (default): Standard for species-level clustering of viruses
- **97-99%**: Stricter, for strain-level distinction
- **90-94%**: More permissive, groups more diverse sequences

### Coverage Threshold (`--min-tcov`)

Target coverage measures what percentage of the shorter sequence is covered by the alignment:

- **85%** (default): Balanced approach
- **90-95%**: More stringent, requires longer alignments
- **70-80%**: More permissive, allows partial matches

!!! tip "Choosing Thresholds"
    - For species-level vOTUs: `--min-ani 95 --min-tcov 85`
    - For strain-level vOTUs: `--min-ani 97 --min-tcov 90`
    - For genus-level grouping: `--min-ani 90 --min-tcov 80`

## Performance Considerations

- **Threads**: Use `-t` to match your CPU cores for faster BLAST
- **Temporary Directory**: Use `--tmp` to specify a fast storage location (SSD or RAM disk)
- **Memory**: Large datasets may require substantial RAM for BLAST operations

## Output

The output FASTA file contains representative sequences from each cluster. The selection criteria:

1. Longest sequence in the cluster (by default)
2. If tied, the one with the most connections
3. If still tied, alphabetically first sequence ID

## Requirements

This command requires:

- BLAST+ toolkit (`blastn` and `makeblastdb`)
- Sufficient disk space in temporary directory for BLAST database and results

## See Also

- [filter](filter.md) - Filter sequences before dereplication
- [Quick Start Guide](../quickstart.md) - Complete workflow examples
