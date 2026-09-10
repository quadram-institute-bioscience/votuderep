# votuderep getdbs

Download geNomad, CheckV, and PHROGs databases for viral sequence analysis.

## Overview

The `getdbs` command simplifies database management by automatically downloading and setting up reference databases needed for viral genomics tools. It supports resumable downloads and validates database integrity.

## Usage

```bash
votuderep getdbs [OPTIONS]
```

### Required Options

- `-o, --outdir PATH` - Directory where to download and extract databases

### Options

- `--force` - Allow using a non-empty output directory
- `--db TEXT` - Database(s) to download: genomad_1.9, checkv_1.5, phrogs_4, or all (default: all). Can be repeated or comma-separated.

## Available Databases

### geNomad 1.9

**Purpose:** Viral identification and classification

**Size:** ~5 GB

**Description:** Database for identifying viruses and plasmids in genomic and metagenomic data using the geNomad tool.

**Reference:** [geNomad GitHub](https://github.com/apcamargo/genomad)

### CheckV 1.5

**Purpose:** Viral genome quality assessment

**Size:** ~1.5 GB

**Description:** Database for assessing the quality and completeness of viral genomes using the CheckV tool.

**Reference:** [CheckV on BitBucket](https://bitbucket.org/berkeleylab/checkv/)

### PHROGs 4

**Purpose:** Viral protein functional annotation

**Size:** ~500 MB

**Description:** Database of Prokaryotic Virus Remote Homologous Groups for annotating viral proteins.

**Reference:** [PHROGs](https://phrogs.lmge.uca.fr/)

## Examples

### Download All Databases

Download all available databases to a directory:

```bash
votuderep getdbs -o ./databases/
```

This will create:
```
databases/
├── genomad_db/
├── checkv-db-v1.5/
└── phrogs/
```

### Download Specific Database

Download only the database you need:

```bash
# Only CheckV
votuderep getdbs -o ./databases/ --db checkv_1.5

# Only geNomad
votuderep getdbs -o ./databases/ --db genomad_1.9

# Only PHROGs
votuderep getdbs -o ./databases/ --db phrogs_4
```

### Force Download to Non-Empty Directory

By default, the command checks if the output directory is empty. Use `--force` to override:

```bash
votuderep getdbs -o ./databases/ --force
```

!!! warning
    Using `--force` in a non-empty directory may overwrite existing files.

### Resume Interrupted Download

Downloads are automatically resumable. If a download is interrupted, simply run the command again:

```bash
# First attempt (interrupted)
votuderep getdbs -o ./databases/ --db checkv_1.5

# Resume (run the same command)
votuderep getdbs -o ./databases/ --db checkv_1.5
```

The command tracks download progress using marker files (`.downloading` and `.done`).

## Download Process

For each database, the command:

1. **Checks for existing complete download** (`.done` marker)
2. **Downloads archive** from the source URL
3. **Validates download** (file size check)
4. **Extracts contents** to the output directory
5. **Creates completion marker** (`.done` file)
6. **Cleans up** temporary files

## Storage Requirements

Make sure you have sufficient disk space:

| Database | Compressed | Extracted | Total Required |
|----------|-----------|-----------|----------------|
| geNomad 1.9 | ~1.5 GB | ~5 GB | ~6.5 GB |
| CheckV 1.5 | ~500 MB | ~1.5 GB | ~2 GB |
| PHROGs 4 | ~200 MB | ~500 MB | ~700 MB |
| **All** | **~2.2 GB** | **~7 GB** | **~9.2 GB** |

!!! tip "Disk Space"
    The command needs space for both the compressed archive and extracted files during installation. After completion, compressed files are automatically deleted.

## Using the Databases

After downloading, use the databases with their respective tools:

### With geNomad

```bash
genomad end-to-end \
  --cleanup \
  --threads 8 \
  contigs.fasta \
  output_dir \
  ./databases/genomad_db
```

### With CheckV

```bash
checkv end_to_end \
  contigs.fasta \
  checkv_output \
  -d ./databases/checkv-db-v1.5 \
  -t 8
```

### With PHROGs

PHROGs is typically used with annotation tools that support the database format. Refer to the PHROGs documentation for integration with specific tools.

## Troubleshooting

### Download Failures

If a download fails repeatedly:

1. Check your internet connection
2. Try downloading a specific database instead of all
3. Check if the source URL is accessible
4. Ensure sufficient disk space

### Corrupted Downloads

If you suspect a corrupted download:

```bash
# Remove the .done marker
rm ./databases/.checkv_1.5.done

# Remove incomplete files
rm -rf ./databases/checkv-db-v1.5/

# Re-download
votuderep getdbs -o ./databases/ --db checkv_1.5
```

### Permission Issues

Ensure you have write permissions in the output directory:

```bash
# Check permissions
ls -ld ./databases/

# Create directory with proper permissions if needed
mkdir -p ./databases/
chmod 755 ./databases/
```

## Database Updates

Database versions are specified in the command. To update to newer versions:

1. Wait for votuderep to support the new version
2. Download to a new directory
3. Update your analysis scripts to use the new database path

!!! note "Version Tracking"
    Each database version is tracked separately, allowing you to maintain multiple versions if needed.

## Network Considerations

### Proxy Settings

If behind a proxy, configure your environment:

```bash
export http_proxy=http://proxy.example.com:8080
export https_proxy=http://proxy.example.com:8080
votuderep getdbs -o ./databases/
```

### Timeout Issues

For slow connections, the command will retry failed downloads automatically with exponential backoff.

## See Also

- [filter](filter.md) - Use CheckV output for filtering
- [Quick Start Guide](../quickstart.md) - Complete workflow with databases
- [Installation](../installation.md) - Setting up votuderep
