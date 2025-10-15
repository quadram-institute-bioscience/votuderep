"""Tests for dereplication functionality."""

from votuderep.core.dereplication import (
    parse_blast_line,
    compute_ani,
    compute_coverage,
    prune_alignments,
)


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
