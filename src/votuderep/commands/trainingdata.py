"""Trainingdata command for downloading training datasets."""

import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, Any

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

# ---------------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------------
# Each dataset is a mapping of arbitrary item keys -> {"url": ..., "path": ...}
# - "url": full remote URL
# - "path": relative output path under the chosen --outdir
#
# Add new datasets by inserting additional top-level keys into DATASETS.
# Avoid special-casing; if paired reads exist, list R1 and R2 explicitly.
DATASETS: Dict[str, Dict[str, Dict[str, str]]] = {
    "virome": {
        # Assembly
        "assembly": {
            "url": "https://zenodo.org/api/records/10650983/files/illumina_sample_pool_megahit.fa.gz/content",
            "path": "human_gut_assembly.fa.gz",
        },
        # Reads: explicit R1/R2 entries (no implicit pairing logic)
        "ERR6797443_R1": {
            "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/003/ERR6797443/ERR6797443_1.fastq.gz",
            "path": "reads/ERR6797443_R1.fastq.gz",
        },
        "ERR6797443_R2": {
            "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/003/ERR6797443/ERR6797443_2.fastq.gz",
            "path": "reads/ERR6797443_R2.fastq.gz",
        },
        "ERR6797444_R1": {
            "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/004/ERR6797444/ERR6797444_1.fastq.gz",
            "path": "reads/ERR6797444_R1.fastq.gz",
        },
        "ERR6797444_R2": {
            "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/004/ERR6797444/ERR6797444_2.fastq.gz",
            "path": "reads/ERR6797444_R2.fastq.gz",
        },
        "ERR6797445_R1": {
            "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/005/ERR6797445/ERR6797445_1.fastq.gz",
            "path": "reads/ERR6797445_R1.fastq.gz",
        },
        "ERR6797445_R2": {
            "url": "ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/005/ERR6797445/ERR6797445_2.fastq.gz",
            "path": "reads/ERR6797445_R2.fastq.gz",
        },
    }
}

console = Console(stderr=True)
logger = get_logger(__name__)


def download_file(url: str, output_path: str, description: str = "Downloading"):
    """Download a file from a URL with progress indication (urllib)."""
    output_file = Path(output_path)
    temp_file = Path(str(output_path) + ".downloading")

    # Check if final file already exists (complete download)
    if output_file.exists():
        logger.info(f"File already exists, skipping download: {output_path}")
        console.print(
            f"[yellow]✓ Skipping {os.path.basename(output_path)} (already exists)[/yellow]"
        )
        return

    # Clean up any partial downloads
    if temp_file.exists():
        logger.info(f"Removing partial download: {temp_file}")
        temp_file.unlink()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"{description} {os.path.basename(output_path)}")

            def reporthook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) / total_size)
                    progress.update(task, completed=percent)

            # Download to temporary file
            urllib.request.urlretrieve(url, str(temp_file), reporthook)
            progress.update(task, completed=100)

        # Rename to final filename on success
        temp_file.rename(output_file)
        logger.info(f"Downloaded: {output_path}")

    except Exception as e:
        # Clean up partial download on failure
        if temp_file.exists():
            temp_file.unlink()
        raise VotuDerepError(f"Failed to download {url}: {e}")


def run_curl(url: str, output_path: str, description: str = "Downloading"):
    """Download a file using curl with progress indication."""
    output_file = Path(output_path)
    temp_file = Path(str(output_path) + ".downloading")

    # Check if final file already exists (complete download)
    if output_file.exists():
        logger.info(f"File already exists, skipping download: {output_path}")
        console.print(
            f"[yellow]✓ Skipping {os.path.basename(output_path)} (already exists)[/yellow]"
        )
        return

    # Clean up any partial downloads
    if temp_file.exists():
        logger.info(f"Removing partial download: {temp_file}")
        temp_file.unlink()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"{description} {os.path.basename(output_path)}")

            # Download to temporary file
            cmd = ["curl", "-L", url, "-o", str(temp_file)]
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            progress.update(task, completed=100)

        # Rename to final filename on success
        temp_file.rename(output_file)
        logger.info(f"Downloaded: {output_path}")

    except subprocess.CalledProcessError as e:
        # Clean up partial download on failure
        if temp_file.exists():
            temp_file.unlink()
        raise VotuDerepError(f"Failed to download {url}: {e.stderr}")
    except FileNotFoundError:
        raise VotuDerepError("curl command not found. Please install curl.")


@click.command(name="trainingdata")
@click.option(
    "-o",
    "--outdir",
    default="./ebame-virome/",
    show_default=True,
    help="Where to put the output files",
)
@click.option(
    "-n",
    "--name",
    "dataset_name",
    default="virome",
    show_default=True,
    help="Dataset name to download (registered in DATASETS)",
)
@click.pass_context
def trainingdata(ctx, outdir: str, dataset_name: str):
    """
    Download training dataset from the internet.

    Uses a registry (DATASETS) of named datasets, each containing a set of
    {url, path} items. Adds new datasets by extending the DATASETS dict.
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        console.print(f"[blue]Output directory:[/blue] {outdir}")
        console.print(f"[blue]Dataset:[/blue] {dataset_name}")

    # Resolve dataset
    dataset: Dict[str, Any] = DATASETS.get(dataset_name)
    if not dataset:
        available = ", ".join(sorted(DATASETS.keys()))
        raise VotuDerepError(f"Unknown dataset '{dataset_name}'. Available datasets: {available}")

    # Create output directory
    outdir_path = Path(outdir)
    try:
        outdir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured base output directory exists: {outdir_path}")

        console.print("[bold green]Downloading training dataset...[/bold green]")

        # Download each item in the dataset
        for key, entry in dataset.items():
            url = entry["url"]
            rel_path = entry["path"]
            dest_path = outdir_path / rel_path

            # Ensure parent directory exists for this entry
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Choose downloader: use curl for ftp URLs; urllib for http(s)
            is_ftp = url.lower().startswith("ftp://")
            console.print(f"\n[blue]Downloading {key}...[/blue]")
            if is_ftp:
                run_curl(url, str(dest_path), f"Downloading {key}")
            else:
                download_file(url, str(dest_path), f"Downloading {key}")

        console.print("\n[bold green]✓ Training dataset downloaded successfully![/bold green]")
        console.print(f"[blue]Files saved to:[/blue] {outdir_path.absolute()}")

        # Summary of downloaded files
        if verbose:
            console.print("\n[bold]Downloaded files:[/bold]")
            for file_path in sorted(outdir_path.rglob("*")):
                if file_path.is_file():
                    size = file_path.stat().st_size / (1024 * 1024)  # MB
                    console.print(f"  • {file_path.relative_to(outdir_path)} ({size:.1f} MB)")

    except Exception as e:
        if isinstance(e, VotuDerepError):
            raise
        else:
            raise VotuDerepError(f"Failed to download training dataset: {e}")
