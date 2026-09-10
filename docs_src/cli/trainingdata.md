# votuderep trainingdata

Download viral assembly and sequencing read datasets for training and testing purposes.

## Overview

The `trainingdata` command downloads example datasets from the EBAME (Empowering Biodiversity through Metagenomics) workshop. These datasets are useful for learning, testing workflows, and benchmarking viral analysis pipelines.

## Usage

```bash
votuderep trainingdata [OPTIONS]
```

### Options

- `-o, --outdir TEXT` - Where to put the output files (default: ./ebame-virome/)
- `-n, --name TEXT` - Dataset name to download (registered in DATASETS) (default: virome)

## Examples

### Download to Default Location

Download all training data to the default directory:

```bash
votuderep trainingdata
```

This creates: `./ebame-virome/`

### Download to Custom Location

Specify a custom output directory:

```bash
votuderep trainingdata -o ./training_data/
```

### With Verbose Output

See detailed progress information:

```bash
votuderep -v trainingdata -o ./data/
```

## Included Datasets

### 1. Viral Assembly

**Source:** Zenodo
**Type:** Assembled viral contigs
**Format:** FASTA
**Description:** Human gut virome assembly for testing viral sequence analysis tools

**Typical Uses:**
- Testing viral identification tools (geNomad, VirSorter)
- Benchmarking CheckV quality assessment
- Testing dereplication with `votuderep derep`
- Practicing filtering with `votuderep filter`

### 2. Sequencing Reads

**Source:** EBI Short Read Archive (SRA)
**Type:** Paired-end sequencing reads
**Format:** FASTQ (gzipped)
**Samples:** 3 samples from human gut virome study

**Sample IDs:**
- ERR6797443 (R1 & R2)
- ERR6797444 (R1 & R2)
- ERR6797445 (R1 & R2)

**Typical Uses:**
- Testing read quality control pipelines
- Practicing assembly workflows
- Benchmarking mapping tools
- Testing `votuderep tabulate` for sample sheet generation

## Output Structure

After downloading, your directory will contain:

```
ebame-virome/
├── assembly/
│   └── viral_contigs.fasta
└── reads/
    ├── ERR6797443_R1.fastq.gz
    ├── ERR6797443_R2.fastq.gz
    ├── ERR6797444_R1.fastq.gz
    ├── ERR6797444_R2.fastq.gz
    ├── ERR6797445_R1.fastq.gz
    └── ERR6797445_R2.fastq.gz
```

## Example Workflows

### Test Complete Pipeline

Use the downloaded data to test a complete viral analysis pipeline:

```bash
# 1. Download training data
votuderep trainingdata -o ./tutorial/

# 2. Run CheckV on the assembly (requires CheckV installed)
checkv end_to_end \
  ./tutorial/assembly/viral_contigs.fasta \
  ./tutorial/checkv_out/ \
  -d ./databases/checkv-db-v1.5

# 3. Filter based on quality
votuderep filter \
  ./tutorial/assembly/viral_contigs.fasta \
  ./tutorial/checkv_out/quality_summary.tsv \
  --min-quality medium \
  -o ./tutorial/filtered.fasta

# 4. Dereplicate
votuderep derep \
  -i ./tutorial/filtered.fasta \
  -o ./tutorial/dereplicated.fasta \
  -t 4
```

### Test Read Processing

Practice working with sequencing reads:

```bash
# 1. Download training data
votuderep trainingdata -o ./tutorial/

# 2. Generate sample sheet
votuderep tabulate ./tutorial/reads/ -o samples.csv

# 3. Run quality control (requires FastQC)
cat samples.csv | tail -n +2 | cut -d',' -f2,3 | tr ',' '\n' | \
  xargs fastqc -o qc_reports/

# 4. Assemble reads (requires assembler like SPAdes or MEGAHIT)
# ... your assembly command ...
```

### Benchmarking

Test performance and compare parameters:

```bash
# Download data
votuderep trainingdata -o ./bench/

# Test different ANI thresholds
for ani in 90 95 97 99; do
  echo "Testing ANI=$ani"
  time votuderep derep \
    -i ./bench/assembly/viral_contigs.fasta \
    -o ./bench/derep_ani${ani}.fasta \
    --min-ani $ani \
    -t 8

  # Count resulting sequences
  grep -c "^>" ./bench/derep_ani${ani}.fasta
done
```

## Dataset Information

### Assembly Dataset

The viral assembly dataset represents typical output from viral contig identification in metagenomic samples. It includes:

- Various contig lengths (representing complete and partial genomes)
- Different quality levels (as would be assessed by CheckV)
- Multiple viral families and diversity

### Read Datasets

The sequencing read datasets are from human gut virome studies and include:

- Paired-end Illumina reads
- Typical read lengths (~150 bp)
- Representative coverage depths
- Real-world complexity and diversity

!!! info "Data Size"
    The complete training dataset is approximately 1-2 GB. Ensure you have sufficient disk space and a stable internet connection for downloading.

## Download Process

The command:

1. **Creates output directory** if it doesn't exist
2. **Downloads assembly** from Zenodo
3. **Downloads reads** from EBI SRA (6 files: 3 samples × 2 reads)
4. **Validates downloads** (checksums where available)
5. **Organizes files** into assembly/ and reads/ subdirectories

Downloads are **resumable** - if interrupted, run the command again to continue.

## Storage Requirements

| Component | Size | Description |
|-----------|------|-------------|
| Assembly | ~100 MB | Viral contigs FASTA |
| Reads (total) | ~1.5 GB | 3 samples, paired-end, gzipped |
| **Total** | **~1.6 GB** | Complete training dataset |

## Using with Workshop Materials

This data is designed to work with the [EBAME workshop](https://maignienlab.gitlab.io/ebame/) materials:

```bash
# Download data
votuderep trainingdata -o ~/ebame_tutorial/

# Follow workshop tutorials using this data
# https://maignienlab.gitlab.io/ebame/
```

## Troubleshooting

### Download Failures

If downloads fail:

1. **Check internet connection**
2. **Verify URLs are accessible** (try in browser)
3. **Run with verbose flag** to see detailed error messages:
   ```bash
   votuderep -v trainingdata
   ```
4. **Resume download** by running the command again

### Disk Space Issues

Ensure sufficient space before downloading:

```bash
# Check available space
df -h .

# If needed, use different location with more space
votuderep trainingdata -o /path/to/larger/disk/
```

### Slow Downloads

For slow connections:

- The command will retry failed downloads automatically
- Consider downloading during off-peak hours
- You can interrupt and resume downloads as needed

### Corrupted Files

If you suspect corrupted downloads:

```bash
# Remove the output directory
rm -rf ./ebame-virome/

# Re-download
votuderep trainingdata
```

## Data Citation

If you use this training data in publications, please cite:

- **EBAME Workshop:** [https://maignienlab.gitlab.io/ebame/](https://maignienlab.gitlab.io/ebame/)
- **Original data sources:** Check the individual dataset repositories on Zenodo and EBI for specific citations

## See Also

- [tabulate](tabulate.md) - Generate sample sheets from the downloaded reads
- [derep](derep.md) - Test dereplication on the assembly
- [filter](filter.md) - Practice filtering with CheckV results
- [Quick Start Guide](../quickstart.md) - Complete workflow examples
