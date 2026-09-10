"""Trainingdata command for downloading training datasets."""

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

console = Console(stderr=True)
logger = get_logger(__name__)

DOWNLOAD_TOOLS = ("curl", "wget")


@dataclass(frozen=True)
class DownloadItem:
    """A file required by the training dataset."""

    url: str
    relative_path: Path
    md5: str
    label: str


TRAINING_DATASET = [
    DownloadItem(
        url="https://zenodo.org/api/records/10650983/files/"
        "illumina_sample_pool_megahit.fa.gz/content",
        relative_path=Path("human_gut_assembly.fa.gz"),
        md5="9c4822401a47e23b3e6623bc786d9fe7",
        label="assembly",
    ),
    DownloadItem(
        url="ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/005/ERR6797445/" "ERR6797445_1.fastq.gz",
        relative_path=Path("reads/ERR6797445_R1.fastq.gz"),
        md5="d28d83a43b464e9a53a97bbd6927c9a4",
        label="ERR6797445_R1",
    ),
    DownloadItem(
        url="ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/005/ERR6797445/" "ERR6797445_2.fastq.gz",
        relative_path=Path("reads/ERR6797445_R2.fastq.gz"),
        md5="acf14bc302765cdbbc01d10705b017ea",
        label="ERR6797445_R2",
    ),
    DownloadItem(
        url="ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/004/ERR6797444/" "ERR6797444_1.fastq.gz",
        relative_path=Path("reads/ERR6797444_R1.fastq.gz"),
        md5="32acaa340451e931da87993e3dffa991",
        label="ERR6797444_R1",
    ),
    DownloadItem(
        url="ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/004/ERR6797444/" "ERR6797444_2.fastq.gz",
        relative_path=Path("reads/ERR6797444_R2.fastq.gz"),
        md5="ee24e0b92b4fb8f588587d0b50db87ed",
        label="ERR6797444_R2",
    ),
    DownloadItem(
        url="ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/003/ERR6797443/" "ERR6797443_1.fastq.gz",
        relative_path=Path("reads/ERR6797443_R1.fastq.gz"),
        md5="d5eaee39a12c249632e4f8d09d98844a",
        label="ERR6797443_R1",
    ),
    DownloadItem(
        url="ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR679/003/ERR6797443/" "ERR6797443_2.fastq.gz",
        relative_path=Path("reads/ERR6797443_R2.fastq.gz"),
        md5="7dac631d14d007788d62e0c94bbe44bd",
        label="ERR6797443_R2",
    ),
]


def select_download_tool(requested_tool: str = "auto") -> str:
    """Select an available command-line downloader."""
    if requested_tool != "auto":
        if requested_tool not in DOWNLOAD_TOOLS:
            raise VotuDerepError(f"Unsupported download tool: {requested_tool}")
        if shutil.which(requested_tool):
            return requested_tool
        raise VotuDerepError(f"{requested_tool} command not found. Please install it.")

    for tool in DOWNLOAD_TOOLS:
        if shutil.which(tool):
            return tool

    raise VotuDerepError("No download tool found. Please install curl or wget.")


def build_download_command(tool: str, url: str, output_path: Path) -> list[str]:
    """Build a downloader command that fails on server-side errors."""
    if tool == "curl":
        return [
            "curl",
            "--fail",
            "--location",
            "--show-error",
            "--silent",
            "--output",
            str(output_path),
            url,
        ]

    if tool == "wget":
        return [
            "wget",
            "--quiet",
            "--tries=1",
            "--output-document",
            str(output_path),
            url,
        ]

    raise VotuDerepError(f"Unsupported download tool: {tool}")


def compute_md5(path: Path) -> str:
    """Compute an MD5 checksum for a file."""
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_md5(path: Path, expected_md5: str):
    """Verify that a downloaded file has the expected MD5 checksum."""
    observed_md5 = compute_md5(path)
    if observed_md5 != expected_md5:
        raise VotuDerepError(
            f"MD5 mismatch for {path}: expected {expected_md5}, got {observed_md5}"
        )


def remove_partial_file(path: Path):
    """Remove an old partial download before starting or retrying."""
    if path.exists():
        path.unlink()


def run_download_command(tool: str, url: str, output_path: Path):
    """Run the selected downloader."""
    cmd = build_download_command(tool, url, output_path)
    subprocess.run(cmd, capture_output=True, text=True, check=True)


def download_item(
    item: DownloadItem,
    outdir: Path,
    tool: str,
    max_retry: int,
    skip_md5: bool,
):
    """Download one item with retry and optional checksum verification."""
    output_path = outdir / item.relative_path
    partial_path = output_path.with_name(f"{output_path.name}.part")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        remove_partial_file(partial_path)
        if skip_md5:
            logger.info(f"Skipping existing file without MD5 verification: {output_path}")
            return output_path

        try:
            verify_md5(output_path, item.md5)
            logger.info(f"Skipping existing verified file: {output_path}")
            return output_path
        except VotuDerepError as e:
            logger.warning(f"Existing file failed MD5 verification and will be replaced: {e}")

    last_error = None

    for attempt in range(1, max_retry + 1):
        remove_partial_file(partial_path)

        try:
            run_download_command(tool, item.url, partial_path)

            if not partial_path.exists():
                raise VotuDerepError(f"Download did not create expected file: {partial_path}")

            if not skip_md5:
                verify_md5(partial_path, item.md5)

            partial_path.replace(output_path)
            logger.info(f"Downloaded: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            last_error = e.stderr.strip() or str(e)
        except (OSError, VotuDerepError) as e:
            last_error = str(e)

        remove_partial_file(partial_path)
        logger.warning(
            f"Download failed for {item.label} (attempt {attempt}/{max_retry}): {last_error}"
        )

    raise VotuDerepError(
        f"Failed to download {item.label} after {max_retry} attempt(s): {last_error}"
    )


@click.command(name="trainingdata")
@click.option(
    "-o",
    "--outdir",
    default="./ebame-virome/",
    show_default=True,
    help="Where to put the output files",
)
@click.option(
    "--download-tool",
    type=click.Choice(["auto", "curl", "wget"]),
    default="auto",
    show_default=True,
    help="Downloader to use",
)
@click.option(
    "--skip-md5",
    is_flag=True,
    help="Skip MD5 checksum verification after download",
)
@click.option(
    "--max-retry",
    type=click.IntRange(1),
    default=5,
    show_default=True,
    help="Maximum download attempts per file",
)
@click.pass_context
def trainingdata(
    ctx,
    outdir: str,
    download_tool: str,
    skip_md5: bool,
    max_retry: int,
):
    """
    Download training dataset from the internet.

    Uses a registry of datasets, each containing a set of
    {url, path} items.
    """
    outdir_path = Path(outdir)
    verbose = (ctx.obj or {}).get("verbose", False)

    try:
        tool = select_download_tool(download_tool)
        outdir_path.mkdir(parents=True, exist_ok=True)

        if verbose:
            console.print(f"[blue]Output directory:[/blue] {outdir}")
            console.print(f"[blue]Download tool:[/blue] {tool}")
            console.print(f"[blue]MD5 verification:[/blue] {'disabled' if skip_md5 else 'enabled'}")

        console.print("[bold green]Downloading training dataset...[/bold green]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Preparing downloads")
            for item in TRAINING_DATASET:
                progress.update(task, description=f"Downloading {item.label}")
                download_item(item, outdir_path, tool, max_retry, skip_md5)

            progress.update(task, description="Downloads complete")

        console.print("\n[bold green]✓ Training dataset downloaded successfully![/bold green]")
        console.print(f"[blue]Files saved to:[/blue] {outdir_path.absolute()}")

        # Summary of downloaded files
        if verbose:
            console.print("\n[bold]Downloaded files:[/bold]")
            for file_path in sorted(outdir_path.rglob("*")):
                if file_path.is_file():
                    size = file_path.stat().st_size / (1024 * 1024)  # MB
                    console.print(f"  \u2022 {file_path.relative_to(outdir_path)} ({size:.1f} MB)")

    except Exception as e:
        if isinstance(e, VotuDerepError):
            raise
        else:
            raise VotuDerepError(f"Failed to download training dataset: {e}")
