"""Tests for n3map.rrfile — RR file parsing, comment patterns, label counters."""

import io
import pytest
import re

from n3map.rrfile import _comment_pattern, RRFileStream
from n3map.exception import FileParseError


class TestCommentPattern:
    """Tests for the _comment_pattern regex (raw-string fix target)."""

    def test_empty_line(self):
        assert re.match(_comment_pattern, "")

    def test_whitespace_only(self):
        assert re.match(_comment_pattern, "   ")

    def test_semicolon_comment(self):
        assert re.match(_comment_pattern, "; this is a comment")

    def test_hash_comment(self):
        assert re.match(_comment_pattern, "# this is a comment")

    def test_indented_semicolon(self):
        assert re.match(_comment_pattern, "   ; indented comment")

    def test_indented_hash(self):
        assert re.match(_comment_pattern, "\t# tab comment")

    def test_data_line_no_match(self):
        assert re.match(_comment_pattern, "example.com. 300 IN NSEC") is None

    def test_tab_whitespace(self):
        assert re.match(_comment_pattern, "\t\t")


class TestLabelCounterRegex:
    """Tests for the label_counter regex in nsec3_reader (raw-string fix target)."""

    def setup_method(self):
        # This is the same regex used in rrfile.py nsec3_reader
        self.p_counter = re.compile(r"^;;;; label_counter\s*=\s*0x([0-9a-fA-F]+)")

    def test_standard_format(self):
        m = self.p_counter.match(";;;; label_counter = 0xdeadbeef")
        assert m is not None
        assert m.group(1) == "deadbeef"

    def test_no_spaces(self):
        m = self.p_counter.match(";;;; label_counter=0x1a2b")
        assert m is not None
        assert m.group(1) == "1a2b"

    def test_extra_spaces(self):
        m = self.p_counter.match(";;;; label_counter   =   0xff")
        assert m is not None
        assert m.group(1) == "ff"

    def test_tab_whitespace(self):
        m = self.p_counter.match(";;;; label_counter\t=\t0xABC")
        assert m is not None
        assert m.group(1) == "ABC"

    def test_uppercase_hex(self):
        m = self.p_counter.match(";;;; label_counter = 0xDEAD")
        assert m is not None
        assert m.group(1) == "DEAD"

    def test_no_match_on_regular_comment(self):
        m = self.p_counter.match("; just a comment")
        assert m is None

    def test_no_match_on_data_line(self):
        m = self.p_counter.match("example.com. 300 IN NSEC3")
        assert m is None


class _FakeFile:
    """Minimal file-like object for testing RRFileStream."""

    def __init__(self, content, name="<test>"):
        self._content = content
        self.name = name

    def __iter__(self):
        return iter(self._content.splitlines(keepends=True))

    def writable(self):
        return False

    def close(self):
        pass


class TestRRFileStreamNSEC3Reader:
    """Integration tests for nsec3_reader parsing."""

    def _make_stream(self, content):
        f = _FakeFile(content)
        return RRFileStream(f)

    def test_reads_label_counter(self):
        content = (
            ";;;; label_counter = 0x42\n"
            "; some comment\n"
        )
        stream = self._make_stream(content)
        records = list(stream.nsec3_reader())
        assert records == []
        assert stream.label_counter == 0x42

    def test_skips_comments(self):
        content = (
            "; header comment\n"
            "# another comment\n"
            "   \n"
        )
        stream = self._make_stream(content)
        records = list(stream.nsec3_reader())
        assert records == []

    def test_invalid_record_raises_file_parse_error(self):
        content = "not-a-valid-record\n"
        stream = self._make_stream(content)
        with pytest.raises(FileParseError):
            list(stream.nsec3_reader())


class TestRRFileStreamNSECReader:
    """Integration tests for nsec_reader parsing."""

    def _make_stream(self, content):
        f = _FakeFile(content)
        return RRFileStream(f)

    def test_skips_comments(self):
        content = (
            "; header\n"
            "# comment\n"
            "\n"
        )
        stream = self._make_stream(content)
        records = list(stream.nsec_reader())
        assert records == []

    def test_invalid_record_raises_file_parse_error(self):
        content = "garbage-data\n"
        stream = self._make_stream(content)
        with pytest.raises(FileParseError):
            list(stream.nsec_reader())
