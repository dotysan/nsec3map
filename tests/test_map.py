"""Tests for n3map.map — _query_interval() and _human_number() regex parsing."""

import pytest

from n3map.map import _query_interval, _human_number, _compute_query_interval


class TestQueryInterval:
    """Tests for the _query_interval regex parser (raw-string fix target)."""

    def test_integer_per_second(self):
        assert _query_interval("10/s") == pytest.approx(0.1)

    def test_integer_per_minute(self):
        assert _query_interval("60/m") == pytest.approx(1.0)

    def test_integer_per_hour(self):
        assert _query_interval("3600/h") == pytest.approx(1.0)

    def test_float_per_second(self):
        # "0.5/s" — the regex must match the literal dot via \.
        assert _query_interval("0.5/s") == pytest.approx(2.0)

    def test_float_large(self):
        assert _query_interval("2.5/s") == pytest.approx(0.4)

    def test_single_digit_dot(self):
        # "1./s" — matches ([0-9]\.) branch
        assert _query_interval("1./s") == pytest.approx(1.0)

    def test_multi_digit_no_dot(self):
        assert _query_interval("100/s") == pytest.approx(0.01)

    def test_invalid_unit_raises(self):
        with pytest.raises(ValueError):
            _query_interval("10/x")

    def test_no_unit_raises(self):
        with pytest.raises(ValueError):
            _query_interval("10")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            _query_interval("")

    def test_zero_rate_raises(self):
        with pytest.raises(ValueError):
            _query_interval("0/s")

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            _query_interval("-1/s")

    def test_letters_in_number_raises(self):
        with pytest.raises(ValueError):
            _query_interval("abc/s")

    def test_dot_only_raises(self):
        with pytest.raises(ValueError):
            _query_interval("./s")


class TestComputeQueryInterval:
    def test_basic(self):
        assert _compute_query_interval(10, 's') == pytest.approx(0.1)

    def test_per_minute(self):
        assert _compute_query_interval(1, 'm') == pytest.approx(60.0)


class TestHumanNumber:
    def test_plain_integer(self):
        assert _human_number("1000") == 1000

    def test_kilo(self):
        assert _human_number("5K") == 5000

    def test_mega(self):
        assert _human_number("2M") == 2_000_000

    def test_giga(self):
        assert _human_number("1G") == 1_000_000_000

    def test_tera(self):
        assert _human_number("1T") == 1_000_000_000_000

    def test_lowercase_unit(self):
        assert _human_number("3k") == 3000

    def test_invalid_unit(self):
        with pytest.raises(ValueError):
            _human_number("5X")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            _human_number("")

    def test_non_numeric_raises(self):
        with pytest.raises(ValueError):
            _human_number("abc")
