"""Getdbs command for downloading genomad and checkv databases."""

import tarfile
import urllib.request
from pathlib import Path

import rich_click as click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

console = Console(stderr=True)
logger = get_logger(__name__)


def download_file_with_marker(
    url: str, output_path: Path, description: str = "Downloading"
) -> bool:
    """
    Download a file from a URL with progress indication.

    Uses .downloading suffix during download, removes it on completion.

    Args:
        url: URL to download from
        output_path: Path where to save the file
        description: Description for progress indicator

    Returns:
        True if downloaded successfully, False if skipped (already exists)

    Raises:
        VotuDerepError: If download fails
    """
    # Path with .downloading suffix for in-progress downloads
    downloading_path = Path(str(output_path) + ".downloading")

    # Check if file already exists (complete download)
    if output_path.exists():
        logger.info(f"Skipping download (already complete): {output_path.name}")
        console.print(
            f"[yellow]⊙[/yellow] Skipping download of {output_path.name} (already exists)"
        )
        return False

    # Clean up any failed download (.downloading file)
    if downloading_path.exists():
        logger.warning(f"Removing failed download: {downloading_path}")
        console.print(f"[yellow]![/yellow] Removing incomplete download: {downloading_path.name}")
        downloading_path.unlink()

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"{description} {output_path.name}")

            def reporthook(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) / total_size)
                    progress.update(task, completed=percent)

            # Download to .downloading file first
            urllib.request.urlretrieve(url, str(downloading_path), reporthook)
            progress.update(task, completed=100)

        # Move to final location (remove .downloading suffix)
        downloading_path.rename(output_path)
        logger.info(f"Downloaded: {output_path}")
        console.print(f"[green]✓[/green] Downloaded {output_path.name}")

        return True

    except Exception as e:
        # Clean up failed download
        if downloading_path.exists():
            downloading_path.unlink()
        raise VotuDerepError(f"Failed to download {url}: {e}")


def extract_tarball(tarball_path: Path, output_dir: Path, description: str = "Extracting") -> bool:
    """
    Extract a tarball to the specified directory.

    Creates .extracted marker file after successful extraction.

    Args:
        tarball_path: Path to the tarball file
        output_dir: Directory where to extract
        description: Description for progress indicator

    Returns:
        True if extracted successfully, False if skipped

    Raises:
        VotuDerepError: If extraction fails
    """
    # Create marker file path (archive_name.extracted in same directory)
    extraction_marker = tarball_path.parent / f"{tarball_path.name}.extracted"

    # Determine the expected extracted directory name
    if tarball_path.name.endswith(".tar.gz"):
        db_name = tarball_path.name[:-7]
    elif tarball_path.name.endswith(".tgz"):
        db_name = tarball_path.name[:-4]
    else:
        db_name = tarball_path.stem

    extracted_dir = output_dir / db_name

    # Check if extraction marker exists (successful extraction)
    if extraction_marker.exists():
        logger.info(f"Skipping extraction (already complete): {db_name}")
        console.print(f"[yellow]⊙[/yellow] Skipping extraction of {db_name} (already extracted)")
        return False

    # If no marker but directory exists, assume failed extraction and clean up
    if extracted_dir.exists() and not extraction_marker.exists():
        logger.warning(f"Found incomplete extraction, removing: {extracted_dir}")
        console.print(f"[yellow]![/yellow] Removing incomplete extraction: {extracted_dir}")
        # Remove the incomplete extraction
        import shutil

        shutil.rmtree(extracted_dir)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(f"{description} {tarball_path.name}")

            # Extract tarball
            with tarfile.open(tarball_path, "r:gz") as tar:
                tar.extractall(path=output_dir)

            progress.update(task, completed=100)

        # Create extraction marker after successful extraction
        extraction_marker.touch()
        logger.info(f"Extracted: {tarball_path} to {output_dir}")
        console.print(f"[green]✓[/green] Extracted {db_name}")

        return True

    except Exception as e:
        # Clean up failed extraction
        if extracted_dir.exists():
            import shutil

            shutil.rmtree(extracted_dir)
        raise VotuDerepError(f"Failed to extract {tarball_path}: {e}")


@click.command(name="getdbs")
@click.option(
    "-o",
    "--outdir",
    required=True,
    type=click.Path(),
    help="Directory where to download and extract databases",
)
@click.option(
    "--force",
    is_flag=True,
    help="Allow using a non-empty output directory",
)
@click.pass_context
def getdbs(ctx, outdir: str, force: bool):
    """
    Download geNomad and CheckV databases for EBAME tutorial.

    Downloads and extracts viral classification and quality control databases
    required for viral metagenomics analysis.

    The command is resumable: if interrupted, it will skip already downloaded
    and extracted files when re-run.

    \b
    Example:
      votuderep getdbs --outdir ~/databases
      votuderep getdbs -o ./db --force
    """
    verbose = ctx.obj.get("verbose", False)

    outdir_path = Path(outdir).resolve()

    if verbose:
        console.print(f"[blue]Output directory:[/blue] {outdir_path}")

    # Check if directory exists and is not empty
    if outdir_path.exists():
        if not outdir_path.is_dir():
            raise VotuDerepError(f"Output path exists but is not a directory: {outdir_path}")

        # Check if directory is not empty
        if any(outdir_path.iterdir()) and not force:
            raise VotuDerepError(
                f"Output directory is not empty: {outdir_path}\n" "Use --force to proceed anyway."
            )
    else:
        # Create output directory
        try:
            outdir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {outdir_path}")
        except Exception as e:
            raise VotuDerepError(f"Failed to create output directory: {e}")

    console.print("[bold green]Downloading databases for EBAME tutorial...[/bold green]\n")

    # Database definitions
    databases = [
        {
            "name": "geNomad",
            "url": "https://ifrqmra-virome.s3.climb.ac.uk/databases/genomad_db.tar.gz",
            "filename": "genomad_db.tar.gz",
        },
        {
            "name": "CheckV",
            "url": "https://ifrqmra-virome.s3.climb.ac.uk/databases/checkv-db-v1.5.tar.gz",
            "filename": "checkv-db-v1.5.tar.gz",
        },
    ]

    downloaded_tarballs = []
    success = True

    try:
        # Download databases
        for db in databases:
            console.print(f"\n[bold blue]Processing {db['name']} database...[/bold blue]")
            tarball_path = outdir_path / db["filename"]

            # Download
            try:
                if download_file_with_marker(db["url"], tarball_path, f"Downloading {db['name']}"):
                    # Only add to list if actually downloaded (not skipped)
                    downloaded_tarballs.append(tarball_path)
            except VotuDerepError as e:
                console.print(f"[red]✗[/red] Failed to download {db['name']}: {e}")
                success = False
                raise

            # Extract
            try:
                extract_tarball(tarball_path, outdir_path, f"Extracting {db['name']}")
            except VotuDerepError as e:
                console.print(f"[red]✗[/red] Failed to extract {db['name']}: {e}")
                success = False
                raise

        # Success! Clean up tarballs (optional - only those we downloaded in this run)
        if success and downloaded_tarballs:
            console.print("\n[bold blue]Cleaning up newly downloaded tarballs...[/bold blue]")
            for tarball_path in downloaded_tarballs:
                if tarball_path.exists():
                    tarball_path.unlink()
                    logger.info(f"Removed tarball: {tarball_path}")
                    console.print(f"[green]✓[/green] Removed {tarball_path.name}")

                    # Also remove the .extracted marker since we removed the archive
                    extraction_marker = tarball_path.parent / f"{tarball_path.name}.extracted"
                    if extraction_marker.exists():
                        extraction_marker.unlink()
                        logger.info(f"Removed marker: {extraction_marker}")

        console.print("\n[bold green]✓ All databases processed successfully![/bold green]")
        console.print(f"[blue]Databases saved to:[/blue] {outdir_path}")

        # Summary
        if verbose:
            console.print("\n[bold]Database directories:[/bold]")
            for item in sorted(outdir_path.iterdir()):
                if item.is_dir() and not item.name.startswith("."):
                    # Calculate directory size
                    total_size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    size_mb = total_size / (1024 * 1024)
                    console.print(f"  • {item.name}/ ({size_mb:.1f} MB)")

    except VotuDerepError as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        console.print(
            "\n[yellow]Note:[/yellow] You can re-run the command to resume from where it stopped."
        )
        raise click.Abort()
    except KeyboardInterrupt:
        console.print(
            "\n[yellow]Interrupted by user[/yellow]\n"
            "You can re-run the command to resume from where it stopped."
        )
        raise click.Abort()
    except Exception as e:
        console.print(f"\n[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        console.print(
            "\n[yellow]Note:[/yellow] You can re-run the command to resume from where it stopped."
        )
        raise click.Abort()
