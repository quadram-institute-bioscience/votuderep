"""Split CoverM command for splitting CoverM TSV by metrics."""

import csv
import gzip
import io
import re
from pathlib import Path
from typing import Dict, List, Tuple

import rich_click as click
from rich.console import Console

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError

console = Console(stderr=True)
logger = get_logger(__name__)


def open_maybe_gzip(path: str, mode: str = "rt", **kwargs):
    """
    Open a file that may be gzipped based on its extension.
    Text mode by default; pass mode='rb' for bytes.
    """
    if path.endswith(".gz"):
        # For text mode, wrap with TextIOWrapper to ensure newline handling
        if "b" in mode:
            return gzip.open(path, mode)
        gz = gzip.open(path, "rb")
        return io.TextIOWrapper(
            gz, encoding=kwargs.get("encoding", "utf-8"), newline=kwargs.get("newline", "")
        )
    return open(path, mode, **kwargs)


def normalize_metric_name(metric: str) -> str:
    """
    Convert header metric names to snake_case filenames.
    Special-cases common CoverM headers to the shorter names requested.
    """
    m = metric.strip().lower()
    # Map known CoverM labels to requested forms
    mapping = {
        "read count": "count",
        "mean": "mean",
        "tpm": "tpm",
        "rpkm": "rpkm",
        "covered fraction": "covered_fraction",
        "covered bases": "covered_bases",
    }
    if m in mapping:
        return mapping[m]
    # Generic fallback: snake_case, alnum + underscore only
    m = m.replace("/", " ").replace("-", " ")
    m = re.sub(r"\s+", "_", m)
    m = re.sub(r"[^a-z0-9_]", "", m)
    return m


def parse_header(header: List[str]) -> Tuple[List[str], List[str], Dict[str, List[int]]]:
    """
    Parse the TSV header.

    Returns:
        samples: list of sample names in the order encountered
        metrics: list of unique metrics (normalized), in the order encountered
        metric_to_indices: map metric_name -> list of column indices for that metric across samples (sample order)
    """
    if not header or header[0] != "Contig":
        raise VotuDerepError("First column must be 'Contig'.")

    samples_order: List[str] = []
    metrics_order: List[str] = []
    metric_to_indices: Dict[str, List[int]] = {}

    # We'll also keep track of which sample order we've established as we see them
    seen_samples = set()

    # From col 1 onward: "<sample> <metric label>"
    for idx, col in enumerate(header[1:], start=1):
        col = col.strip()
        if not col:
            continue
        if " " not in col:
            # If the column doesn't have a space, we can't split sample vs metric reliably
            # Treat the whole thing as a metric with an implicit single sample
            sample_name, raw_metric = "sample", col
        else:
            sample_name, raw_metric = col.split(" ", 1)

        if sample_name not in seen_samples:
            samples_order.append(sample_name)
            seen_samples.add(sample_name)

        metric_norm = normalize_metric_name(raw_metric)
        if metric_norm not in metrics_order:
            metrics_order.append(metric_norm)
        metric_to_indices.setdefault(metric_norm, []).append(idx)

    # Sanity check: each metric should have as many indices as samples
    for m in metrics_order:
        if len(metric_to_indices[m]) != len(samples_order):
            # Not fatal; warn to stderr
            logger.warning(
                f"Metric '{m}' has {len(metric_to_indices[m])} columns but {len(samples_order)} samples."
            )

    return samples_order, metrics_order, metric_to_indices


def split_coverm_table(input_file: str, output_basename: str, verbose: bool = False):
    """
    Split a CoverM TSV by metric into separate TSVs, one per metric.

    Args:
        input_file: Input CoverM TSV (optionally gzipped: .gz)
        output_basename: Output basename/prefix for generated files
        verbose: Enable verbose logging

    Returns:
        List of output file paths created

    Raises:
        VotuDerepError: If input file is empty or malformed
    """
    # Check if input file exists
    input_path = Path(input_file)
    if not input_path.exists():
        raise VotuDerepError(f"Input file does not exist: {input_file}")

    # Read header first
    with open_maybe_gzip(input_file, mode="rt", newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration:
            raise VotuDerepError("Input file is empty.")

        samples, metrics, metric_to_indices = parse_header(header)

        if verbose:
            logger.info(f"Found {len(samples)} samples and {len(metrics)} metrics")
            logger.info(f"Samples: {', '.join(samples)}")
            logger.info(f"Metrics: {', '.join(metrics)}")

        # Prepare writers: one file per metric
        writers: Dict[str, csv.writer] = {}
        files: Dict[str, io.TextIOBase] = {}
        output_files: List[str] = []

        try:
            for metric in metrics:
                out_path = f"{output_basename}_{metric}.tsv"
                output_files.append(out_path)
                f = open(out_path, "w", newline="", encoding="utf-8")
                files[metric] = f
                w = csv.writer(f, delimiter="\t", lineterminator="\n")
                writers[metric] = w
                # Header: Contig + one column per sample
                w.writerow(["Contig"] + samples)

            # Process rows and write one line per metric
            row_count = 0
            for row in reader:
                if not row:
                    continue
                row_count += 1
                contig = row[0]
                for metric in metrics:
                    indices = metric_to_indices.get(metric, [])
                    values = []
                    for idx in indices:
                        # If row is shorter than expected, pad with empty
                        values.append(row[idx] if idx < len(row) else "")
                    writers[metric].writerow([contig] + values)

            if verbose:
                logger.info(f"Processed {row_count} contigs")

        finally:
            for f in files.values():
                try:
                    f.close()
                except Exception:
                    pass

    return output_files


@click.command(name="splitcoverm")
@click.option(
    "-i",
    "--input",
    "input_file",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
    help="Input CoverM TSV (optionally gzipped: .gz)",
)
@click.option(
    "-o",
    "--output-basename",
    "basename",
    type=str,
    required=True,
    help="Output basename/prefix for generated files",
)
@click.pass_context
def splitcoverm(ctx, input_file: str, basename: str):
    """
    Split a CoverM TSV by metric into separate TSVs, one per metric.

    Reads a CoverM output table containing multiple metrics across samples
    and splits it into individual TSV files, one for each metric.
    Each output file will have the format: <basename>_<metric>.tsv

    The input TSV is expected to have columns formatted as:
    "Contig", "<sample1> <metric1>", "<sample1> <metric2>", ...

    \b
    Example:
      votuderep splitcoverm -i coverage.tsv -o output/cov
      votuderep splitcoverm -i coverage.tsv.gz -o results/sample
    """
    verbose = ctx.obj.get("verbose", False)

    if verbose:
        console.print(f"[blue]Input file:[/blue] {input_file}")
        console.print(f"[blue]Output basename:[/blue] {basename}")

    try:
        output_files = split_coverm_table(input_file, basename, verbose)

        console.print("\n[bold green]Success![/bold green]")
        console.print(f"Split CoverM table into {len(output_files)} metric files:")
        for out_file in output_files:
            console.print(f"  • {out_file}")

    except VotuDerepError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise click.Abort()
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        raise click.Abort()
