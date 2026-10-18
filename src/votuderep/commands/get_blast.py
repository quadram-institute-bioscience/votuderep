"""Get-blast command for downloading and installing BLAST+ binaries."""

import html.parser
import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
from pathlib import Path

import rich_click as click
from rich.console import Console

from ..utils.logging import get_logger
from ..utils.validators import VotuDerepError
from .getdbs import download_file_with_marker

console = Console(stderr=True)
logger = get_logger(__name__)

BASE_URL = "https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/"

# (system, machine) → tarball suffix
_PLATFORM_MAP = {
    ("darwin", "arm64"): "aarch64-macosx",
    ("darwin", "x86_64"): "x64-macosx",
    ("linux", "x86_64"): "x64-linux",
    ("linux", "aarch64"): "aarch64-linux",
    ("linux", "arm64"): "aarch64-linux",  # some distros report arm64
}


def _detect_suffix() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    suffix = _PLATFORM_MAP.get((system, machine))
    if not suffix:
        supported = ", ".join(f"{s}/{m}" for s, m in _PLATFORM_MAP)
        raise VotuDerepError(f"Unsupported platform: {system}/{machine}\nSupported: {supported}")
    return suffix


class _LinkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for attr, val in attrs:
                if attr == "href" and val:
                    self.links.append(val)


def _fetch_tarball_info(suffix: str) -> tuple[str, str]:
    """Return (filename, url) for the latest BLAST+ tarball matching *suffix*."""
    try:
        with urllib.request.urlopen(BASE_URL, timeout=30) as resp:
            html_content = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise VotuDerepError(f"Failed to fetch NCBI BLAST directory listing: {e}")

    parser = _LinkParser()
    parser.feed(html_content)

    for link in parser.links:
        name = link.strip("/")
        if suffix in name and name.endswith(".tar.gz") and not name.endswith(".md5"):
            return name, BASE_URL + name

    raise VotuDerepError(
        f"Could not find a BLAST+ tarball for platform suffix '{suffix}' at {BASE_URL}"
    )


def _install_candidates() -> list[Path]:
    """
    Return candidate install directories in priority order, deduplicated:
      a) Directory containing the votuderep CLI entrypoint
      b) Writable directories in $PATH
      c) Current working directory
    """
    seen: set[Path] = set()
    candidates: list[Path] = []

    def _add(p: Path):
        resolved = p.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(resolved)

    # a) Same dir as CLI entrypoint
    cli_path = shutil.which("votuderep")
    if cli_path:
        _add(Path(cli_path).parent)

    # b) Writable dirs in $PATH
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        p = Path(entry)
        if p.is_dir() and os.access(p, os.W_OK):
            _add(p)

    # c) Current working directory
    _add(Path.cwd())

    return candidates


def _extract_bins(tarball: Path, dest_dir: Path) -> list[Path]:
    """
    Extract only the bin/* binaries from the BLAST+ tarball into dest_dir.
    Returns list of installed paths.
    """
    installed: list[Path] = []
    with tarfile.open(tarball, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            parts = Path(member.name).parts
            # Structure: ncbi-blast-X.Y.Z+/bin/<binary>
            if len(parts) >= 3 and parts[1] == "bin":
                binary_name = parts[2]
                # Rewrite path so it extracts flat into dest_dir
                member.name = binary_name
                tar.extract(member, path=dest_dir)
                dest = dest_dir / binary_name
                dest.chmod(0o755)
                installed.append(dest)
    return installed


@click.command(name="get-blast")
@click.option(
    "-o",
    "--outdir",
    default=None,
    type=click.Path(),
    help="Install BLAST+ binaries into this directory (always downloads, even if blast is in PATH).",
)
@click.pass_context
def get_blast(ctx, outdir: str | None):
    """
    Download and install BLAST+ binaries for the current platform.

    Fetches the latest BLAST+ release from NCBI and installs the binaries.
    Without -o, installation is attempted in the following order:

    \b
      1. Same directory as the votuderep CLI entrypoint
      2. First writable directory in $PATH
      3. Current working directory

    \b
    With -o OUTDIR, binaries are always installed into OUTDIR, even if
    blastn is already in PATH.
    """
    verbose = ctx.obj.get("verbose", False)

    # Detect platform
    suffix = _detect_suffix()
    console.print(
        f"[blue]Platform:[/blue] {platform.system()} {platform.machine()} "
        f"→ [bold]{suffix}[/bold]"
    )

    # Resolve the tarball name and URL from NCBI
    console.print("[blue]Fetching latest release info from NCBI...[/blue]")
    filename, url = _fetch_tarball_info(suffix)
    console.print(f"[blue]Latest BLAST+:[/blue] {filename}")

    if outdir is not None:
        # Explicit destination: always install, no PATH check
        install_dir = Path(outdir).resolve()
        install_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[blue]Install directory:[/blue] {install_dir}")
    else:
        # Auto-detect: pick first writable candidate, skip if already present
        candidates = _install_candidates()
        if verbose:
            console.print("[blue]Install candidates (in priority order):[/blue]")
            for c in candidates:
                writable = os.access(c, os.W_OK)
                mark = "[green]writable[/green]" if writable else "[red]read-only[/red]"
                console.print(f"  • {c}  ({mark})")

        install_dir = next(
            (c for c in candidates if c.is_dir() and os.access(c, os.W_OK)),
            None,
        )
        if install_dir is None:
            raise VotuDerepError(
                "No writable installation directory found among candidates:\n"
                + "\n".join(f"  {c}" for c in candidates)
            )

        console.print(f"[blue]Install directory:[/blue] {install_dir}")

        if (install_dir / "blastn").exists():
            console.print(
                f"[yellow]⊙[/yellow] blastn already found in {install_dir} — nothing to do."
            )
            return

    # Download into a temp dir, then extract
    with tempfile.TemporaryDirectory() as tmpdir:
        tarball_path = Path(tmpdir) / filename
        console.print()
        download_file_with_marker(url, tarball_path, "Downloading")

        console.print(f"\n[blue]Extracting binaries into {install_dir}...[/blue]")
        installed = _extract_bins(tarball_path, install_dir)

    if not installed:
        raise VotuDerepError("No binaries were found inside the tarball.")

    console.print(
        f"\n[bold green]✓ Installed {len(installed)} BLAST+ binaries to {install_dir}[/bold green]"
    )
    if verbose:
        for p in sorted(installed, key=lambda x: x.name):
            console.print(f"  • {p.name}")

    # Warn if install_dir is not in PATH
    path_dirs = {Path(d).resolve() for d in os.environ.get("PATH", "").split(os.pathsep)}
    if install_dir not in path_dirs:
        console.print(
            f"\n[yellow]⚠[/yellow] [bold]{install_dir}[/bold] is not in $PATH.\n"
            f'  Add it with:  export PATH="{install_dir}:$PATH"'
        )
