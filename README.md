# votuderep

[![Test](https://github.com/quadram-institute-bioscience/votuderep/actions/workflows/test.yml/badge.svg)](https://github.com/quadram-institute-bioscience/votuderep/actions/workflows/test.yml)


![Logo](votuderep.png)

A Python CLI tool for dereplicating and filtering viral contigs (vOTUs - viral Operational Taxonomic Units)
using the CheckV method.

## Features

- **Dereplicate vOTUs**: Remove redundant viral sequences using BLAST-based ANI clustering
- **Filter by CheckV metrics**: Filter viral contigs based on quality, completeness, and other metrics
- **Tabulate reads**: Generate CSV tables from paired-end sequencing read directories
- **Download training data**: Fetch viral assembly datasets for training purposes

## Requirements

- Python >= 3.10
- BLAST+ toolkit (specifically `blastn` and `makeblastdb`)

## Installation

### From source

```bash
# Clone the repository
git clone https://github.com/yourusername/votuderep.git
cd votuderep

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Installing BLAST+

votuderep requires BLAST+ to be installed and available in your PATH:

```bash
# Using conda (recommended)
conda install -c bioconda blast

# On Ubuntu/Debian
sudo apt-get install ncbi-blast+

# On macOS
brew install blast
```


## Usage

votuderep provides four main commands: `derep`, `filter`, `tabulate`, and `trainingdata`.

### Dereplicate vOTUs

Remove redundant sequences using BLAST and ANI clustering:

```bash
votuderep derep -i input.fasta -o dereplicated.fasta
```

**Options:**

- `-i, --input`: Input FASTA file [required]
- `-o, --output`: Output FASTA file [default: dereplicated_vOTUs.fasta]
- `-t, --threads`: Number of threads for BLAST [default: 2]
- `--tmp`: Temporary directory [default: $TEMP or /tmp]
- `--min-ani`: Minimum ANI threshold (0-100) [default: 95]
- `--min-tcov`: Minimum target coverage (0-100) [default: 85]
- `--keep`: Keep temporary directory with intermediate files

**Example:**

```bash
# Basic dereplication
votuderep derep -i viral_contigs.fasta -o dereplicated.fasta

# With custom parameters
votuderep derep -i viral_contigs.fasta -o dereplicated.fasta \
  --min-ani 97 --min-tcov 90 -t 8

# Keep intermediate files for inspection
votuderep derep -i viral_contigs.fasta -o dereplicated.fasta \
  --keep --tmp ./temp_dir
```

**How it works:**

1. Creates a BLAST database from input sequences
2. Performs all-vs-all BLASTN comparison
3. Calculates ANI (Average Nucleotide Identity) and coverage
4. Clusters sequences using greedy centroid-based algorithm
5. Outputs the longest sequence from each cluster (representative)

### Filter by CheckV

Filter viral contigs based on CheckV quality metrics:

```bash
votuderep filter input.fasta checkv_output.tsv -o filtered.fasta
```

**Required Arguments:**

- `FASTA`: Input FASTA file with viral contigs
- `CHECKV_OUT`: TSV output file from CheckV

**Options:**

**Length filters:**
- `-m, --min-len`: Minimum contig length [default: 0]
- `--max-len`: Maximum contig length, 0 = unlimited [default: 0]

**Quality filters:**
- `--min-quality`: Minimum quality level: low, medium, or high [default: low]
- `--complete`: Only keep complete genomes
- `--exclude-undetermined`: Exclude contigs where quality is "Not-determined"

**Metrics filters:**
- `-c, --min-completeness`: Minimum completeness percentage (0-100)
- `--max-contam`: Maximum contamination percentage (0-100)
- `--no-warnings`: Only keep contigs with no warnings

**Other filters:**
- `--provirus`: Only select proviruses (provirus == "Yes")
- `-o, --output`: Output FASTA file [default: STDOUT]

**Examples:**

```bash
# Basic filtering - minimum quality
votuderep filter viral_contigs.fasta checkv_output.tsv -o filtered.fasta

# High-quality sequences only
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --min-quality high -o high_quality.fasta

# Complete genomes with minimum length
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --complete --min-len 5000 -o complete_genomes.fasta

# Complex filtering
votuderep filter viral_contigs.fasta checkv_output.tsv \
  --min-quality medium \
  --min-completeness 80 \
  --max-contam 5 \
  --no-warnings \
  --min-len 3000 \
  -o high_confidence.fasta

# Output to stdout (for piping)
votuderep filter viral_contigs.fasta checkv_output.tsv > filtered.fasta
```

**Quality Levels:**

CheckV assigns quality levels to viral contigs:

- **Complete**: Complete genomes (highest quality)
- **High-quality**: High confidence viral sequences
- **Medium-quality**: Moderate confidence sequences
- **Low-quality**: Lower confidence but valid sequences
- **Not-determined**: Quality could not be determined

The `--min-quality` option filters inclusively:
- `low`: Includes Low, Medium, High, and Complete (default)
- `medium`: Includes Medium, High, and Complete
- `high`: Includes High and Complete only

Note: "Not-determined" sequences are included by default unless `--exclude-undetermined` is used.

### Tabulate Reads

Generate a CSV table from a directory containing paired-end sequencing reads:

```bash
votuderep tabulate reads/ -o samples.csv
```

**Required Arguments:**

- `INPUT_DIR`: Directory containing sequencing read files

**Options:**

- `-o, --output`: Output CSV file [default: STDOUT]
- `-d, --delimiter`: Field separator [default: ,]
- `-1, --for-tag`: Forward read identifier [default: _R1]
- `-2, --rev-tag`: Reverse read identifier [default: _R2]
- `-s, --strip`: Remove string from sample names (can be used multiple times)
- `-e, --extension`: Only process files with this extension
- `-a, --absolute`: Use absolute paths in output

**Examples:**

```bash
# Basic usage - generate CSV table
votuderep tabulate reads/ -o samples.csv

# Custom read tags and extension
votuderep tabulate reads/ --for-tag _1 --rev-tag _2 --extension .fq.gz

# Strip patterns from sample names and use absolute paths
votuderep tabulate reads/ --strip "Sample_" --strip ".filtered" -a
```

### Download Training Data

Download viral assembly and sequencing reads for training purposes:

```bash
votuderep trainingdata -o ./ebame-virome/
```

**Options:**

- `-o, --outdir`: Output directory [default: ./ebame-virome/]

**Example:**

```bash
# Download to default directory
votuderep trainingdata

# Download to custom directory
votuderep trainingdata -o ./training_data/
```

## Global Options

- `-v, --verbose`: Enable verbose logging
- `--version`: Show version and exit
- `--help`: Show help message

## License

MIT License - See LICENSE file for details

 
## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Authors

Andrea Telatin & QIB Core Bioinformatics

©️ Quadram Institute Bioscience 2025
 
