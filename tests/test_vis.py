"""Tests for n3map.vis — strvis/strunvis encoding."""

import pytest

from n3map.vis import strvis, strunvis, vis


class TestVis:
    def test_printable_is_visible(self):
        assert vis(ord(b"A")) is True

    def test_null_is_not_visible(self):
        assert vis(0) is False


class TestStrvis:
    def test_ascii_unchanged(self):
        assert strvis(b"hello") == b"hello"

    def test_backslash_doubled(self):
        assert strvis(b"a\\b") == b"a\\\\b"

    def test_non_printable_hex_encoded(self):
        result = strvis(b"\x00")
        assert result == b"\\x00"

    def test_high_byte_encoded(self):
        result = strvis(b"\xff")
        assert result == b"\\xff"

    def test_mixed(self):
        result = strvis(b"a\x01b")
        assert result == b"a\\x01b"


class TestStrunvis:
    def test_plain_ascii(self):
        assert strunvis(b"hello") == b"hello"

    def test_hex_escape(self):
        assert strunvis(b"\\x41") == b"A"

    def test_double_backslash(self):
        assert strunvis(b"a\\\\b") == b"a\\b"

    def test_roundtrip(self):
        original = b"\x00\x01hello\xffworld"
        assert strunvis(strvis(original)) == original

    def test_invalid_escape_raises(self):
        with pytest.raises(ValueError):
            strunvis(b"\\q")

    def test_trailing_backslash_raises(self):
        with pytest.raises(ValueError):
            strunvis(b"abc\\")
