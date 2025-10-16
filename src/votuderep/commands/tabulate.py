"""Tabulate command for generating CSV files from reads directories."""

from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

import rich_click as click
from rich.console import Console

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

console = Console(stderr=True)
logger = get_logger(__name__)


def extract_sample_name(
    filename: str, for_tag: str, rev_tag: str, strip_strings: List[str]
) -> Optional[tuple[str, str]]:
    """
    Extract sample name from filename.

    Args:
        filename: The filename to process
        for_tag: Forward reads tag (e.g., "_R1")
        rev_tag: Reverse reads tag (e.g., "_R2")
        strip_strings: List of strings to remove from filename

    Returns:
        Tuple of (sample_name, read_type) or None if no tag found
        read_type is either "R1" or "R2"
    """
    # Start with the basename
    basename = filename

    # Remove all strip strings
    for strip_str in strip_strings:
        basename = basename.replace(strip_str, "")

    # Check for forward or reverse tag
    read_type = None
    sample_name = None

    if for_tag in basename:
        # Split on for_tag and take everything before it
        sample_name = basename.split(for_tag)[0]
        read_type = "R1"
    elif rev_tag in basename:
        # Split on rev_tag and take everything before it
        sample_name = basename.split(rev_tag)[0]
        read_type = "R2"

    if sample_name and read_type:
        return (sample_name, read_type)
    return None


def scan_directory(
    input_dir: Path,
    extension: str,
    for_tag: str,
    rev_tag: str,
    strip_strings: List[str],
    use_absolute: bool,
) -> Dict[str, Dict[str, str]]:
    """
    Scan directory for read files and organize them by sample.

    Args:
        input_dir: Directory to scan
        extension: File extension filter
        for_tag: Forward reads identifier
        rev_tag: Reverse reads identifier
        strip_strings: Strings to remove from sample names
        use_absolute: Whether to use absolute paths

    Returns:
        Dictionary mapping sample names to their R1/R2 files

    Raises:
        VotuDerepError: If directory doesn't exist, no files match, or duplicates found
    """
    if not input_dir.exists():
        raise VotuDerepError(f"Input directory does not exist: {input_dir}")

    if not input_dir.is_dir():
        raise VotuDerepError(f"Input path is not a directory: {input_dir}")

    # Data structure to store samples
    samples: Dict[str, Dict[str, str]] = defaultdict(dict)
    seen_files: Dict[str, List[str]] = defaultdict(list)

    # Scan directory
    files_processed = 0
    files_matched = 0

    for file_path in sorted(input_dir.iterdir()):
        if not file_path.is_file():
            continue

        files_processed += 1
        filename = file_path.name

        # Check extension filter
        if extension and not filename.endswith(extension):
            logger.debug(f"Skipping {filename} (does not match extension: {extension})")
            continue

        # Extract sample name and read type
        result = extract_sample_name(filename, for_tag, rev_tag, strip_strings)

        if result is None:
            logger.debug(f"Skipping {filename} (no read tag found)")
            continue

        sample_name, read_type = result
        files_matched += 1

        # Get the file path (absolute or relative)
        if use_absolute:
            file_path_str = str(file_path.absolute())
        else:
            file_path_str = str(file_path)

        # Check for duplicate sample/read_type combinations
        if read_type in samples[sample_name]:
            raise VotuDerepError(
                f"Duplicate files found for sample '{sample_name}' {read_type}: "
                f"{samples[sample_name][read_type]} and {file_path_str}"
            )

        samples[sample_name][read_type] = file_path_str
        seen_files[sample_name].append(filename)

    logger.info(f"Processed {files_processed} files, matched {files_matched} read files")

    if files_matched == 0:
        raise VotuDerepError(
            f"No files matched the criteria in {input_dir}. "
            f"Check --extension, --for-tag, and --rev-tag options."
        )

    return dict(samples)


@click.command(name="tabulate")
@click.argument("input_dir", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False),
    default=None,
    help="Output CSV file (default: STDOUT)",
)
@click.option(
    "-d",
    "--delimiter",
    type=str,
    default=",",
    show_default=True,
    help="Field separator",
)
@click.option(
    "-1",
    "--for-tag",
    type=str,
    default="_R1",
    show_default=True,
    help="Identifier for forward reads",
)
@click.option(
    "-2",
    "--rev-tag",
    type=str,
    default="_R2",
    show_default=True,
    help="Identifier for reverse reads",
)
@click.option(
    "-s",
    "--strip",
    "strip_strings",
    type=str,
    multiple=True,
    help="Remove this string from sample names (can be used multiple times)",
)
@click.option(
    "-e",
    "--extension",
    type=str,
    default="",
    help="Only process files ending with this extension",
)
@click.option(
    "-a",
    "--absolute",
    is_flag=True,
    help="Use absolute paths in output",
)
@click.pass_context
def tabulate(
    ctx,
    input_dir: str,
    output: Optional[str],
    delimiter: str,
    for_tag: str,
    rev_tag: str,
    strip_strings: tuple,
    extension: str,
    absolute: bool,
):
    """
    Generate CSV file from a directory containing sequencing reads.

    Scans INPUT_DIR for paired-end sequencing reads and generates a CSV table
    mapping sample names to their R1 and R2 file paths.

    The command identifies read pairs by looking for forward/reverse tags in filenames,
    extracts sample names, and outputs a table suitable for downstream analysis tools.

    \b
    Example:
      votuderep tabulate reads/ -o samples.csv
      votuderep tabulate reads/ --for-tag _1 --rev-tag _2 --extension .fq.gz
      votuderep tabulate reads/ --strip "Sample_" --strip ".filtered" -a
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        console.print(f"[blue]Input directory:[/blue] {input_dir}")
        console.print(f"[blue]Extension filter:[/blue] {extension if extension else '(none)'}")
        console.print(f"[blue]Forward tag:[/blue] {for_tag}")
        console.print(f"[blue]Reverse tag:[/blue] {rev_tag}")
        if strip_strings:
            console.print(f"[blue]Strip strings:[/blue] {', '.join(strip_strings)}")

    try:
        # Scan directory and build sample table
        input_path = Path(input_dir)
        samples = scan_directory(
            input_path,
            extension,
            for_tag,
            rev_tag,
            list(strip_strings),
            absolute,
        )

        # Sort samples alphabetically
        sorted_samples = sorted(samples.keys())

        # Prepare output
        output_lines = []
        header = f"sampleID{delimiter}reads_R1{delimiter}reads_R2"
        output_lines.append(header)

        for sample_name in sorted_samples:
            r1_path = samples[sample_name].get("R1", "")
            r2_path = samples[sample_name].get("R2", "")
            line = f"{sample_name}{delimiter}{r1_path}{delimiter}{r2_path}"
            output_lines.append(line)

        # Write output
        if output:
            with open(output, "w") as f:
                f.write("\n".join(output_lines) + "\n")
            console.print("\n[bold green]Success![/bold green]")
            console.print(f"Tabulated {len(sorted_samples)} samples")
            console.print(f"Output written to: [bold]{output}[/bold]")
        else:
            # Write to stdout
            for line in output_lines:
                print(line)
            console.print("\n[bold green]Success![/bold green]", style="green")
            console.print(f"Tabulated {len(sorted_samples)} samples to STDOUT")

        # Show warnings for unpaired samples
        unpaired = []
        for sample_name in sorted_samples:
            if "R1" not in samples[sample_name] or "R2" not in samples[sample_name]:
                unpaired.append(sample_name)

        if unpaired and verbose:
            console.print(f"\n[yellow]Warning:[/yellow] {len(unpaired)} sample(s) are unpaired:")
            for sample in unpaired:
                missing = []
                if "R1" not in samples[sample]:
                    missing.append("R1")
                if "R2" not in samples[sample]:
                    missing.append("R2")
                console.print(f"  • {sample} (missing: {', '.join(missing)})")

    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise click.Abort()
