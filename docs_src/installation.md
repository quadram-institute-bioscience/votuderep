# Installation

## Requirements

- Python >= 3.10
- BLAST+ toolkit (specifically `blastn` and `makeblastdb`)

## Installing votuderep

### From PyPI (Recommended)

```bash
pip install votuderep
```

### From Conda/Bioconda

```bash
conda install -c bioconda votuderep
```

### From Source

```bash
# Clone the repository
git clone https://github.com/quadram-institute-bioscience/votuderep.git
cd votuderep

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

## Installing BLAST+

votuderep requires BLAST+ to be installed and available in your PATH for the `derep` command:

### Using conda (recommended)

```bash
conda install -c bioconda blast
```

### On Ubuntu/Debian

```bash
sudo apt-get install ncbi-blast+
```

### On macOS

```bash
brew install blast
```

### Verify Installation

After installation, verify that BLAST+ is available:

```bash
blastn -version
makeblastdb -version
```

## Optional Dependencies

### Development Dependencies

If you're contributing to the project or want to run tests:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest
- pytest-cov
- black (code formatter)
- ruff (linter)

### Documentation Dependencies

To build the documentation locally:

```bash
pip install -e ".[docs]"
```

This includes:
- mkdocs
- mkdocs-material
- mkdocstrings
- mkdocs-click

## Verifying Installation

After installation, verify that votuderep is available:

```bash
votuderep --version
votuderep --help
```

You should see the version information and available commands.

## Troubleshooting

### Command not found

If you get a "command not found" error after installation:

1. Make sure your Python scripts directory is in your PATH
2. Try using `python -m votuderep` instead of `votuderep`
3. If installed with `--user`, add `~/.local/bin` to your PATH

### BLAST+ not found

If votuderep can't find BLAST+ tools:

1. Verify BLAST+ is installed: `which blastn`
2. Ensure your PATH includes the BLAST+ installation directory
3. Consider using conda to install BLAST+ in the same environment

## Next Steps

Once installation is complete, check out the [Quick Start Guide](quickstart.md) to start using votuderep.
