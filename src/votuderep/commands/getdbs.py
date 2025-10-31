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


def move_to_destination(source_path: Path, dest_dir: Path) -> bool:
    """
    Move a downloaded file to its destination directory.

    Used for files that don't need extraction (e.g., TSV files).

    Args:
        source_path: Path to the source file
        dest_dir: Destination directory

    Returns:
        True if moved successfully, False if already exists

    Raises:
        VotuDerepError: If move fails
    """
    # Create destination directory if it doesn't exist
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / source_path.name

    # Check if file already exists at destination
    if dest_path.exists():
        logger.info(f"File already at destination: {dest_path}")
        # Remove the source file since it's not needed
        if source_path.exists() and source_path != dest_path:
            source_path.unlink()
        return False

    try:
        # Move file to destination
        source_path.rename(dest_path)
        logger.info(f"Moved: {source_path.name} to {dest_dir}")
        console.print(f"[green]✓[/green] Moved {source_path.name} to destination")
        return True

    except Exception as e:
        raise VotuDerepError(f"Failed to move {source_path} to {dest_dir}: {e}")


def extract_tarball(
    tarball_path: Path,
    output_dir: Path,
    description: str = "Extracting",
    extract_to: Path | None = None,
) -> bool:
    """
    Extract a tarball to the specified directory.

    Creates .extracted marker file after successful extraction.

    Args:
        tarball_path: Path to the tarball file
        output_dir: Directory where to extract (base directory)
        description: Description for progress indicator
        extract_to: Optional subdirectory path to extract into (relative to output_dir)

    Returns:
        True if extracted successfully, False if skipped

    Raises:
        VotuDerepError: If extraction fails
    """
    # If extract_to is specified, use it as the extraction directory
    if extract_to:
        final_output_dir = extract_to
        # Create the subdirectory if it doesn't exist
        final_output_dir.mkdir(parents=True, exist_ok=True)
    else:
        final_output_dir = output_dir

    # Create marker file path (archive_name.extracted in same directory as tarball)
    extraction_marker = tarball_path.parent / f"{tarball_path.name}.extracted"

    # For tracking purposes, determine the database name
    if tarball_path.name.endswith(".tar.gz"):
        db_name = tarball_path.name[:-7]
    elif tarball_path.name.endswith(".tgz"):
        db_name = tarball_path.name[:-4]
    else:
        db_name = tarball_path.stem

    # When extracting to a subdirectory, we don't create a separate db_name folder
    # The contents are extracted directly into the extract_to directory
    if extract_to:
        extracted_dir = final_output_dir
    else:
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
                tar.extractall(path=final_output_dir)

            progress.update(task, completed=100)

        # Create extraction marker after successful extraction
        extraction_marker.touch()
        logger.info(f"Extracted: {tarball_path} to {final_output_dir}")
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
@click.option(
    "--db",
    multiple=True,
    help="Database(s) to download: genomad_1.9, checkv_1.5, phrogs_4, or all (default: all). Can be repeated or comma-separated.",
)
@click.pass_context
def getdbs(ctx, outdir: str, force: bool, db: tuple):
    """
    Download geNomad, CheckV, and PHROGs databases.

    Downloads and extracts viral classification and quality control databases
    required for viral metagenomics analysis.

    The command is resumable: if interrupted, it will skip already downloaded
    and extracted files when re-run.

    \b
    Available databases:
      genomad_1.9  - geNomad viral identification database
      checkv_1.5   - CheckV viral quality control database
      phrogs_4     - PHROGs viral protein families database
      all          - Download all databases (default)

    \b
    Examples:
      votuderep getdbs --outdir ~/databases
      votuderep getdbs -o ./db --db genomad_1.9 --db checkv_1.5
      votuderep getdbs -o ./db --db genomad_1.9,checkv_1.5
      votuderep getdbs -o ./db --db all
    """
    verbose = ctx.obj.get("verbose", False)

    # Parse database selections (support repeated flags, comma-separated, and space-separated values)
    selected_dbs = []
    if db:
        for item in db:
            # Handle comma-separated and space-separated values
            # First split by comma, then by space
            for part in item.replace(",", " ").split():
                if part:  # Skip empty strings
                    selected_dbs.append(part)

    # Default to "all" if nothing specified
    if not selected_dbs:
        selected_dbs = ["all"]
        console.print("[yellow]⚠[/yellow] No databases specified, defaulting to --db all")

    # Validate database names
    valid_dbs = {"genomad_1.9", "checkv_1.5", "phrogs_4", "all"}
    invalid_dbs = set(selected_dbs) - valid_dbs
    if invalid_dbs:
        raise VotuDerepError(
            f"Invalid database name(s): {', '.join(invalid_dbs)}\n"
            f"Valid options: {', '.join(sorted(valid_dbs))}"
        )

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

    console.print("[bold green]Downloading databases...[/bold green]\n")

    # Database definitions
    all_databases = {
        "genomad_1.9": {
            "display_name": "geNomad 1.9",
            "files": [
                {
                    "url": "https://ifrqmra-virome.s3.climb.ac.uk/databases/genomad_db.tar.gz",
                    "filename": "genomad_db.tar.gz",
                    "extract": True,
                    "extract_to": None,  # Extract to outdir root
                }
            ],
        },
        "checkv_1.5": {
            "display_name": "CheckV 1.5",
            "files": [
                {
                    "url": "https://ifrqmra-virome.s3.climb.ac.uk/databases/checkv-db-v1.5.tar.gz",
                    "filename": "checkv-db-v1.5.tar.gz",
                    "extract": True,
                    "extract_to": None,  # Extract to outdir root
                }
            ],
        },
        "phrogs_4": {
            "display_name": "PHROGs 4",
            "files": [
                {
                    "url": "https://phrogs.lmge.uca.fr/downloads_from_website/FAA_phrog.tar.gz",
                    "filename": "FAA_phrog.tar.gz",
                    "extract": True,
                    "extract_to": "phrogs",  # Extract inside phrogs subdirectory
                },
                {
                    "url": "https://phrogs.lmge.uca.fr/downloads_from_website/MSA_phrogs.tar.gz",
                    "filename": "MSA_phrogs.tar.gz",
                    "extract": True,
                    "extract_to": "phrogs",
                },
                {
                    "url": "https://phrogs.lmge.uca.fr/downloads_from_website/HMM_phrog.tar.gz",
                    "filename": "HMM_phrog.tar.gz",
                    "extract": True,
                    "extract_to": "phrogs",
                },
                {
                    "url": "https://phrogs.lmge.uca.fr/downloads_from_website/FAA_singletons.tar.gz",
                    "filename": "FAA_singletons.tar.gz",
                    "extract": True,
                    "extract_to": "phrogs",
                },
                {
                    "url": "https://phrogs.lmge.uca.fr/downloads_from_website/phrog_annot_v4.tsv",
                    "filename": "phrog_annot_v4.tsv",
                    "extract": False,  # Don't extract, it's a TSV file
                    "extract_to": "phrogs",
                },
            ],
        },
    }

    # Determine which databases to process
    if "all" in selected_dbs:
        databases_to_process = list(all_databases.keys())
    else:
        databases_to_process = selected_dbs

    if verbose:
        console.print(f"[blue]Selected databases:[/blue] {', '.join(databases_to_process)}\n")

    downloaded_tarballs = []
    success = True

    try:
        # Process each selected database
        for db_key in databases_to_process:
            db_config = all_databases[db_key]
            console.print(
                f"\n[bold blue]Processing {db_config['display_name']} database...[/bold blue]"
            )

            # Process each file in the database
            for file_config in db_config["files"]:
                file_path = outdir_path / file_config["filename"]

                # Download the file
                try:
                    downloaded = download_file_with_marker(
                        file_config["url"],
                        file_path,
                        f"Downloading {file_config['filename']}",
                    )
                    if downloaded:
                        downloaded_tarballs.append(file_path)
                except VotuDerepError as e:
                    console.print(f"[red]✗[/red] Failed to download {file_config['filename']}: {e}")
                    success = False
                    raise

                # Extract or move the file based on its type
                if file_config["extract"]:
                    # It's an archive - extract it
                    try:
                        extract_to_path = None
                        if file_config["extract_to"]:
                            extract_to_path = outdir_path / file_config["extract_to"]

                        extract_tarball(
                            file_path,
                            outdir_path,
                            f"Extracting {file_config['filename']}",
                            extract_to=extract_to_path,
                        )
                    except VotuDerepError as e:
                        console.print(
                            f"[red]✗[/red] Failed to extract {file_config['filename']}: {e}"
                        )
                        success = False
                        raise
                else:
                    # It's a regular file - move it to destination
                    try:
                        dest_dir = outdir_path
                        if file_config["extract_to"]:
                            dest_dir = outdir_path / file_config["extract_to"]
                        move_to_destination(file_path, dest_dir)
                    except VotuDerepError as e:
                        console.print(f"[red]✗[/red] Failed to move {file_config['filename']}: {e}")
                        success = False
                        raise

        # Success! Clean up tarballs (optional - only those we downloaded in this run)
        if success and downloaded_tarballs:
            console.print("\n[bold blue]Cleaning up newly downloaded archives...[/bold blue]")
            for tarball_path in downloaded_tarballs:
                if tarball_path.exists():
                    tarball_path.unlink()
                    logger.info(f"Removed archive: {tarball_path}")
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
