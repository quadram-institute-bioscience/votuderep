"""Tests for dereplication functionality."""

import gzip
import textwrap
import pytest
from click.testing import CliRunner

from votuderep.core.dereplication import (
    parse_blast_line,
    compute_ani,
    compute_coverage,
    prune_alignments,
    yield_alignment_blocks,
    calculate_ani,
    cluster_by_ani,
)
from votuderep.commands.derep import derep
from votuderep.commands.filter import filter_cmd


def _make_cli():
    """Return a fresh cli group with derep and filter registered."""
    from votuderep.cli import cli as _cli

    # Commands are idempotent to add; safe to call repeatedly in tests
    if "derep" not in _cli.commands:
        _cli.add_command(derep)
    if "filter" not in _cli.commands:
        _cli.add_command(filter_cmd)
    return _cli


class TestBlastParsing:
    """Test BLAST output parsing."""

    def test_parse_blast_line(self):
        """Test parsing a BLAST output line."""
        line = "seq1\tseq2\t95.5\t100\t4\t0\t1\t100\t1\t100\t1e-50\t200\t1000\t1200"
        result = parse_blast_line(line)

        assert result["qname"] == "seq1"
        assert result["tname"] == "seq2"
        assert result["pid"] == 95.5
        assert result["len"] == 100.0
        assert result["qlen"] == 1000.0
        assert result["tlen"] == 1200.0
        assert result["evalue"] == 1e-50


class TestANICalculation:
    """Test ANI calculation."""

    def test_compute_ani(self):
        """Test ANI computation from alignments."""
        alns = [{"len": 100, "pid": 95.0}, {"len": 50, "pid": 90.0}]
        ani = compute_ani(alns)
        expected = (100 * 95.0 + 50 * 90.0) / (100 + 50)
        assert ani == round(expected, 2)

    def test_compute_ani_empty(self):
        """Test ANI computation with empty alignments."""
        alns = []
        ani = compute_ani(alns)
        assert ani == 0.0


class TestCoverageCalculation:
    """Test coverage calculation."""

    def test_compute_coverage_non_overlapping(self):
        """Test coverage with non-overlapping alignments."""
        alns = [
            {"qcoords": [1, 100], "tcoords": [1, 100], "qlen": 1000.0, "tlen": 1200.0},
            {"qcoords": [201, 300], "tcoords": [201, 300], "qlen": 1000.0, "tlen": 1200.0},
        ]
        qcov, tcov = compute_coverage(alns)
        # 200 bases covered out of 1000
        assert qcov == 20.0
        # 200 bases covered out of 1200
        assert tcov == round(200.0 / 1200.0 * 100, 2)

    def test_compute_coverage_overlapping(self):
        """Test coverage with overlapping alignments."""
        alns = [
            {"qcoords": [1, 100], "tcoords": [1, 100], "qlen": 1000.0, "tlen": 1000.0},
            {"qcoords": [50, 150], "tcoords": [50, 150], "qlen": 1000.0, "tlen": 1000.0},
        ]
        qcov, tcov = compute_coverage(alns)
        # Should merge to 1-150 = 150 bases
        assert qcov == 15.0
        assert tcov == 15.0


class TestAlignmentPruning:
    """Test alignment pruning."""

    def test_prune_by_length(self):
        """Test pruning by minimum length."""
        alns = [
            {"qcoords": [1, 100], "len": 100, "evalue": 1e-10, "qlen": 1000},
            {"qcoords": [201, 210], "len": 10, "evalue": 1e-10, "qlen": 1000},
        ]
        pruned = prune_alignments(alns, min_length=50)
        assert len(pruned) == 1
        assert pruned[0]["len"] == 100

    def test_prune_by_evalue(self):
        """Test pruning by e-value."""
        alns = [
            {"qcoords": [1, 100], "len": 100, "evalue": 1e-10, "qlen": 1000},
            {"qcoords": [201, 300], "len": 100, "evalue": 1e-1, "qlen": 1000},
        ]
        pruned = prune_alignments(alns, min_evalue=1e-3)
        assert len(pruned) == 1
        assert pruned[0]["evalue"] == 1e-10

    def test_prune_empty_input(self):
        """Test that an empty alignment list returns empty without error."""
        assert prune_alignments([]) == []


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

BLAST_LINE = "seq1\tseq2\t95.5\t500\t4\t0\t1\t500\t1\t500\t1e-50\t900\t1000\t1200"

BLAST_LINE_SELF = "seq1\tseq1\t100.0\t1000\t0\t0\t1\t1000\t1\t1000\t0.0\t2000\t1000\t1000"

FASTA_TWO_SEQS = textwrap.dedent("""\
    >seq1
    ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
    >seq2
    ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT
""")

FASTA_ONE_SEQ = textwrap.dedent("""\
    >seq1
    ATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCG
""")

ANI_HEADER = "qname\ttname\tnum_alns\tpid\tqcov\ttcov\n"


# ---------------------------------------------------------------------------
# Empty BLAST file
# ---------------------------------------------------------------------------


class TestEmptyBlastFile:
    """Behaviour when BLAST output is empty."""

    def test_yield_alignment_blocks_empty(self, tmp_path):
        """yield_alignment_blocks on an empty file produces no blocks."""
        empty = tmp_path / "empty.tsv"
        empty.write_text("")
        blocks = list(yield_alignment_blocks(str(empty)))
        assert blocks == []

    def test_yield_alignment_blocks_empty_gz(self, tmp_path):
        """yield_alignment_blocks on an empty gzip file produces no blocks."""
        empty = tmp_path / "empty.tsv.gz"
        with gzip.open(empty, "wt") as fh:
            fh.write("")
        blocks = list(yield_alignment_blocks(str(empty)))
        assert blocks == []

    def test_calculate_ani_empty_blast(self, tmp_path):
        """calculate_ani on an empty BLAST file writes only the header."""
        blast = tmp_path / "blast.tsv"
        blast.write_text("")
        out = tmp_path / "ani.tsv"
        calculate_ani(str(blast), str(out))
        lines = out.read_text().splitlines()
        assert lines == ["qname\ttname\tnum_alns\tpid\tqcov\ttcov"]


# ---------------------------------------------------------------------------
# Malformed BLAST lines
# ---------------------------------------------------------------------------


class TestMalformedBlastLines:
    """Parsing failures surface with clear Python errors (no silent data corruption)."""

    def test_too_few_fields_raises(self):
        """A line with fewer than 14 fields raises IndexError."""
        short_line = "seq1\tseq2\t95.5\t100"
        with pytest.raises((IndexError, ValueError)):
            parse_blast_line(short_line)

    def test_non_numeric_pid_raises(self):
        """A non-numeric percent-identity raises ValueError."""
        bad_line = "seq1\tseq2\tXX\t100\t4\t0\t1\t100\t1\t100\t1e-50\t200\t1000\t1200"
        with pytest.raises(ValueError):
            parse_blast_line(bad_line)

    def test_non_numeric_evalue_raises(self):
        """A non-numeric evalue raises ValueError."""
        bad_line = "seq1\tseq2\t95.5\t100\t4\t0\t1\t100\t1\t100\tBAD\t200\t1000\t1200"
        with pytest.raises(ValueError):
            parse_blast_line(bad_line)

    def test_yield_blocks_single_pair(self, tmp_path):
        """A file with a single alignment yields exactly one block."""
        blast = tmp_path / "single.tsv"
        blast.write_text(BLAST_LINE + "\n")
        blocks = list(yield_alignment_blocks(str(blast)))
        assert len(blocks) == 1
        assert len(blocks[0]) == 1

    def test_yield_blocks_groups_same_pair(self, tmp_path):
        """Multiple lines for the same query-target pair form one block."""
        blast = tmp_path / "multi.tsv"
        blast.write_text(BLAST_LINE + "\n" + BLAST_LINE + "\n")
        blocks = list(yield_alignment_blocks(str(blast)))
        assert len(blocks) == 1
        assert len(blocks[0]) == 2


# ---------------------------------------------------------------------------
# Single-sequence input
# ---------------------------------------------------------------------------


class TestSingleSequenceInput:
    """A FASTA with one sequence should yield itself as the sole representative."""

    def test_cluster_single_sequence(self, tmp_path):
        """Single sequence → one cluster, itself as centroid, no edges needed."""
        fasta = tmp_path / "single.fasta"
        fasta.write_text(FASTA_ONE_SEQ)

        # ANI file with only the header (self-match filtered, no homologs)
        ani = tmp_path / "ani.tsv"
        ani.write_text(ANI_HEADER)

        clusters = cluster_by_ani(str(fasta), str(ani))
        assert list(clusters.keys()) == ["seq1"]
        assert clusters["seq1"] == ["seq1"]

    def test_cluster_single_sequence_self_match_ignored(self, tmp_path):
        """Self-match in ANI file is skipped; sequence still forms its own cluster."""
        fasta = tmp_path / "single.fasta"
        fasta.write_text(FASTA_ONE_SEQ)

        ani = tmp_path / "ani.tsv"
        ani.write_text(ANI_HEADER + "seq1\tseq1\t1\t100.0\t100.0\t100.0\n")

        clusters = cluster_by_ani(str(fasta), str(ani))
        assert "seq1" in clusters
        assert len(clusters) == 1


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


class TestCLIIntegration:
    """End-to-end CLI tests that do not require external binaries."""

    def test_derep_missing_blastn(self, tmp_path):
        """derep aborts cleanly when blastn is not on PATH."""
        import os

        fasta = tmp_path / "input.fasta"
        fasta.write_text(FASTA_TWO_SEQS)

        runner = CliRunner()
        env = {k: v for k, v in os.environ.items()}
        env["PATH"] = str(tmp_path)  # no blastn on PATH
        result = runner.invoke(
            _make_cli(),
            ["derep", "-i", str(fasta), "-o", str(tmp_path / "out.fasta")],
            env=env,
            obj={},
        )
        assert result.exit_code != 0

    def test_derep_missing_input_file(self, tmp_path):
        """derep aborts when the input file does not exist."""
        runner = CliRunner()
        result = runner.invoke(
            _make_cli(),
            ["derep", "-i", str(tmp_path / "nonexistent.fasta"), "-o", str(tmp_path / "out.fasta")],
            obj={},
        )
        assert result.exit_code != 0

    def test_filter_help(self):
        """filter --help exits cleanly."""
        runner = CliRunner()
        result = runner.invoke(_make_cli(), ["filter", "--help"], obj={})
        assert result.exit_code == 0
        assert "filter" in result.output.lower()

    def test_derep_help(self):
        """derep --help exits cleanly and mentions expected options."""
        runner = CliRunner()
        result = runner.invoke(_make_cli(), ["derep", "--help"], obj={})
        assert result.exit_code == 0
        assert "--min-ani" in result.output
