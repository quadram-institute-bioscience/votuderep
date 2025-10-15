"""Tests for filtering functionality."""

import pytest

from votuderep.core.filtering import parse_quality_threshold, filter_by_checkv, QUALITY_LEVELS


class TestQualityParsing:
    """Test quality threshold parsing."""

    def test_parse_quality_low(self):
        """Test parsing 'low' quality threshold."""
        result = parse_quality_threshold("low")
        assert result == 2

    def test_parse_quality_medium(self):
        """Test parsing 'medium' quality threshold."""
        result = parse_quality_threshold("medium")
        assert result == 3

    def test_parse_quality_high(self):
        """Test parsing 'high' quality threshold."""
        result = parse_quality_threshold("high")
        assert result == 4

    def test_parse_quality_invalid(self):
        """Test parsing invalid quality threshold."""
        with pytest.raises(ValueError):
            parse_quality_threshold("invalid")


class TestQualityLevels:
    """Test quality level definitions."""

    def test_quality_hierarchy(self):
        """Test that quality levels are properly ordered."""
        assert QUALITY_LEVELS["Complete"] > QUALITY_LEVELS["High-quality"]
        assert QUALITY_LEVELS["High-quality"] > QUALITY_LEVELS["Medium-quality"]
        assert QUALITY_LEVELS["Medium-quality"] > QUALITY_LEVELS["Low-quality"]
        assert QUALITY_LEVELS["Low-quality"] > QUALITY_LEVELS["Not-determined"]


class TestCheckvFiltering:
    """Test CheckV filtering functionality."""

    @pytest.fixture
    def sample_checkv_data(self, tmp_path):
        """Create a sample CheckV TSV file."""
        data = """contig_id\tcontig_length\tprovirus\tproviral_length\tgene_count\tviral_genes\thost_genes\tcheckv_quality\tmiuvig_quality\tcompleteness\tcompleteness_method\tcontamination\tkmer_freq\twarnings
seq1\t10000\tNo\tNA\t10\t10\t0\tComplete\tComplete\t100.0\tmethod1\t0.0\t1.0\t
seq2\t8000\tYes\t5000\t8\t8\t0\tHigh-quality\tHigh-quality\t90.0\tmethod1\t0.5\t1.0\t
seq3\t3000\tNo\tNA\t3\t3\t0\tMedium-quality\tMedium-quality\t50.0\tmethod1\t1.0\t1.0\t
seq4\t2000\tNo\tNA\t2\t2\t0\tLow-quality\tLow-quality\t30.0\tmethod1\t2.0\t1.0\twarning1
seq5\t1000\tNo\tNA\t1\t1\t0\tLow-quality\tLow-quality\t20.0\tmethod1\t0.0\t0.5\t
seq6\t15000\tNo\tNA\t15\t15\t0\tComplete\tComplete\t100.0\tmethod1\t0.0\t1.0\t
seq7\t500\tNo\tNA\t1\t1\t0\tNot-determined\tNA\tNA\tNA\tNA\t0.5\t"""

        checkv_file = tmp_path / "checkv.tsv"
        checkv_file.write_text(data)
        return str(checkv_file)

    def test_filter_min_length(self, sample_checkv_data):
        """Test filtering by minimum length."""
        result = filter_by_checkv(sample_checkv_data, min_len=5000)
        assert "seq1" in result  # 10000 bp
        assert "seq2" in result  # 8000 bp
        assert "seq6" in result  # 15000 bp
        assert "seq3" not in result  # 3000 bp
        assert "seq4" not in result  # 2000 bp

    def test_filter_max_length(self, sample_checkv_data):
        """Test filtering by maximum length."""
        result = filter_by_checkv(sample_checkv_data, max_len=5000)
        assert "seq3" in result  # 3000 bp
        assert "seq4" in result  # 2000 bp
        assert "seq5" in result  # 1000 bp
        assert "seq1" not in result  # 10000 bp
        assert "seq2" not in result  # 8000 bp

    def test_filter_provirus_only(self, sample_checkv_data):
        """Test filtering for proviruses only."""
        result = filter_by_checkv(sample_checkv_data, provirus_only=True)
        assert "seq2" in result  # provirus
        assert "seq1" not in result  # not provirus
        assert "seq3" not in result  # not provirus

    def test_filter_min_completeness(self, sample_checkv_data):
        """Test filtering by minimum completeness."""
        result = filter_by_checkv(sample_checkv_data, min_completeness=80.0)
        assert "seq1" in result  # 100%
        assert "seq2" in result  # 90%
        assert "seq3" not in result  # 50%
        assert "seq4" not in result  # 30%

    def test_filter_max_contamination(self, sample_checkv_data):
        """Test filtering by maximum contamination."""
        result = filter_by_checkv(sample_checkv_data, max_contam=1.0)
        assert "seq1" in result  # 0.0%
        assert "seq2" in result  # 0.5%
        assert "seq3" in result  # 1.0%
        assert "seq4" not in result  # 2.0%

    def test_filter_no_warnings(self, sample_checkv_data):
        """Test filtering for sequences with no warnings."""
        result = filter_by_checkv(sample_checkv_data, no_warnings=True)
        assert "seq1" in result  # no warnings
        assert "seq2" in result  # no warnings
        assert "seq4" not in result  # has warning

    def test_filter_complete_only(self, sample_checkv_data):
        """Test filtering for complete genomes only."""
        result = filter_by_checkv(sample_checkv_data, complete_only=True)
        assert "seq1" in result  # Complete
        assert "seq6" in result  # Complete
        assert "seq2" not in result  # High-quality
        assert "seq3" not in result  # Medium-quality

    def test_filter_min_quality_high(self, sample_checkv_data):
        """Test filtering for high quality."""
        result = filter_by_checkv(sample_checkv_data, min_quality="high")
        assert "seq1" in result  # Complete
        assert "seq2" in result  # High-quality
        assert "seq6" in result  # Complete
        assert "seq3" not in result  # Medium-quality
        assert "seq4" not in result  # Low-quality

    def test_filter_min_quality_medium(self, sample_checkv_data):
        """Test filtering for medium quality and above."""
        result = filter_by_checkv(sample_checkv_data, min_quality="medium")
        assert "seq1" in result  # Complete
        assert "seq2" in result  # High-quality
        assert "seq3" in result  # Medium-quality
        assert "seq6" in result  # Complete
        assert "seq4" not in result  # Low-quality

    def test_filter_exclude_undetermined(self, sample_checkv_data):
        """Test excluding undetermined quality sequences."""
        result = filter_by_checkv(sample_checkv_data, exclude_undetermined=True, min_quality="low")
        assert "seq7" not in result  # Not-determined
        assert "seq1" in result  # Complete
        assert "seq4" in result  # Low-quality

    def test_filter_combined(self, sample_checkv_data):
        """Test combining multiple filters."""
        result = filter_by_checkv(
            sample_checkv_data, min_len=3000, min_quality="medium", no_warnings=True
        )
        assert "seq1" in result  # Passes all filters
        assert "seq2" in result  # Passes all filters
        assert "seq3" in result  # Passes all filters
        assert "seq6" in result  # Passes all filters
        assert "seq4" not in result  # Has warning and too short
        assert "seq5" not in result  # Too short and quality too low
