"""Trainingdata command for downloading training datasets."""

import logging
import os
import subprocess
import urllib.request
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

console = Console(stderr=True)
logger = get_logger(__name__)


def download_file(url: str, output_path: str, description: str = "Downloading"):
    """Download a file from a URL with progress indication."""
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
            
            urllib.request.urlretrieve(url, output_path, reporthook)
            progress.update(task, completed=100)
            
        logger.info(f"Downloaded: {output_path}")
        
    except Exception as e:
        raise VotuDerepError(f"Failed to download {url}: {e}")


def run_curl(url: str, output_path: str, description: str = "Downloading"):
    """Download a file using curl with progress indication."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"{description} {os.path.basename(output_path)}")
            
            cmd = ["curl", "-L", url, "-o", output_path]
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            progress.update(task, completed=100)
            
        logger.info(f"Downloaded: {output_path}")
        
    except subprocess.CalledProcessError as e:
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
@click.pass_context
def trainingdata(ctx, outdir: str):
    """
    Download training dataset from the internet.
    
    Downloads viral assembly and sequencing reads for training purposes.
    """
    verbose = ctx.obj.get("verbose", False)
    
    if verbose:
        console.print(f"[blue]Output directory:[/blue] {outdir}")
    
    # Create output directory structure
    outdir_path = Path(outdir)
    reads_dir = outdir_path / "reads"
    
    try:
        reads_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory structure: {reads_dir}")
        
        console.print("[bold green]Downloading training dataset...[/bold green]")
        
        # Download assembly
        assembly_url = "https://zenodo.org/api/records/10650983/files/illumina_sample_pool_megahit.fa.gz/content"
        assembly_path = outdir_path / "human_gut_assembly.fa.gz"
        
        console.print("\n[blue]Downloading assembly...[/blue]")
        download_file(assembly_url, str(assembly_path), "Downloading assembly")
        
        # Download reads
        console.print("\n[blue]Downloading sequencing reads...[/blue]")
        ebi_base = "ftp://ftp.sra.ebi.ac.uk/vol1/fastq"
        
        reads_to_download = [
            ("ERR6797445", "ERR679/005/ERR6797445"),
            ("ERR6797444", "ERR679/004/ERR6797444"), 
            ("ERR6797443", "ERR679/003/ERR6797443"),
        ]
        
        for sample_id, path_suffix in reads_to_download:
            for read_num in ["1", "2"]:
                url = f"{ebi_base}/{path_suffix}/{sample_id}_{read_num}.fastq.gz"
                output_file = reads_dir / f"{sample_id}_R{read_num}.fastq.gz"
                
                run_curl(url, str(output_file), f"Downloading {sample_id}_R{read_num}")
        
        console.print(f"\n[bold green]✓ Training dataset downloaded successfully![/bold green]")
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