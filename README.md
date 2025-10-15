# votuderep

A Python CLI tool for dereplicating and filtering viral contigs (vOTUs - viral Operational Taxonomic Units).

## Features

- **Dereplicate vOTUs**: Remove redundant viral sequences using BLAST-based ANI clustering
- **Filter by CheckV metrics**: Filter viral contigs based on quality, completeness, and other metrics
- **Rich CLI interface**: Beautiful, user-friendly command-line interface powered by rich-click
- **Modular design**: Well-structured codebase with separation of concerns
- **Type-safe**: Written with type hints for better code quality

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

Alternatively, download from [NCBI](https://blast.ncbi.nlm.nih.gov/Blast.cgi?PAGE_TYPE=BlastDocs&DOC_TYPE=Download).

## Usage

votuderep provides two main commands: `derep` and `filter`.

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

## Global Options

- `-v, --verbose`: Enable verbose logging
- `--version`: Show version and exit
- `--help`: Show help message

## Project Structure

```
votuderep/
├── pyproject.toml          # Modern Python packaging configuration
├── README.md               # This file
├── src/
│   └── votuderep/
│       ├── __init__.py     # Package initialization
│       ├── __main__.py     # Entry point for python -m votuderep
│       ├── cli.py          # Main CLI setup
│       ├── commands/       # Subcommands
│       │   ├── __init__.py
│       │   ├── derep.py    # Dereplication command
│       │   └── filter.py   # Filtering command
│       ├── core/           # Business logic
│       │   ├── __init__.py
│       │   ├── blast.py    # BLAST operations
│       │   ├── dereplication.py  # ANI calculation and clustering
│       │   └── filtering.py      # CheckV filtering logic
│       └── utils/          # Utilities
│           ├── __init__.py
│           ├── validators.py  # Input validation
│           ├── io.py          # File I/O helpers
│           └── logging.py     # Logging setup
└── tests/                  # Test suite
    ├── test_derep.py
    └── test_filter.py
```

## Development

### Install development dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Code formatting

```bash
# Format code
black src/

# Lint code
ruff check src/
```

## Environment Variables

- `VOTUDEREP_BLASTN_PATH`: Custom path to blastn executable

## License

MIT License - See LICENSE file for details

## Citation

If you use votuderep in your research, please cite:

```
[Citation information to be added]
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Authors

- Your Name (your.email@example.com)

## Acknowledgments

- BLAST+ for sequence comparison
- CheckV for viral genome quality assessment
- Rich and rich-click for beautiful CLI output
