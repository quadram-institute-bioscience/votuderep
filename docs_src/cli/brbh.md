# votuderep brbh

Find Best Reciprocal Best Hits (BRBH) between two nucleotide FASTA files.

## Overview

The `brbh` command identifies reciprocal best BLASTN hits between two sets of sequences. A pair (A, B) is a BRBH when sequence A's best hit in the target is B, and B's best hit in the query is A. This is a standard proxy for orthology in comparative genomics (Ward & Moreno-Hagelsieb 2014).

Typical uses:

- Comparing viral genomes across two samples or assemblies
- Identifying conserved sequences between datasets
- Ortholog detection for downstream phylogenomics

Both input files may be gzip-compressed (`.gz`).

## Usage

```bash
votuderep brbh [OPTIONS] QUERY TARGET
```

### Arguments

- `QUERY` - Query nucleotide FASTA file
- `TARGET` - Target nucleotide FASTA file

### Required Options

- `-o, --outdir PATH` - Output directory (created if absent)

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `-b, --basename TEXT` | `<query>_vs_<target>` | Basename for output files |
| `--tmp TEXT` | `$TEMP` or `/tmp` | Directory for temporary files |
| `-t, --threads INT` | `2` | BLAST threads |
| `--evalue FLOAT` | `1e-5` | Maximum e-value for BLAST hits |
| `--min-cov FLOAT` | `50.0` | Minimum coverage of query OR target (%) |
| `--keep` | off | Keep temporary BLAST files after completion |

## Output Files

Three files are written to `OUTDIR`:

| File | Description |
|------|-------------|
| `{basename}_rbh.tsv` | RBH pairs table (query, target, %id, bitscore, evalue, qlen, tlen, qcov, tcov, aln_len) |
| `{basename}_query.fasta` | Query sequences that have a reciprocal hit |
| `{basename}_target.fasta` | Target sequences that have a reciprocal hit |

## Examples

### Basic Usage

```bash
votuderep brbh genome_a.fasta genome_b.fasta -o results/
```

### Gzipped Inputs with Custom Basename

```bash
votuderep brbh a.fasta.gz b.fasta.gz -o results/ -b a_vs_b -t 8
```

### Stricter Filtering

```bash
votuderep brbh query.fna target.fna -o out/ --evalue 1e-10 --min-cov 70
```

### Keep Intermediate BLAST Files

```bash
votuderep brbh query.fasta target.fasta -o results/ --keep --tmp ./tmp/
```

## Algorithm

1. Decompress inputs if gzip-compressed
2. Validate that inputs contain nucleotide sequences
3. Build BLAST databases for both query and target
4. Run forward BLAST (query → target)
5. Run reverse BLAST (target → query)
6. For each query sequence, find the top hit; for each target sequence, find the top hit
7. A pair is a BRBH if both sequences are each other's best hit and both pass `--min-cov` and `--evalue` filters
8. Write results table and filtered FASTA files

## See Also

- [derep](derep.md) - Dereplicate a single set of viral sequences
- [Quick Start Guide](../quickstart.md)
