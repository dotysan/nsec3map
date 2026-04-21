"""Tests for n3map.util — base32 extended hex encoding/decoding."""

import pytest

from n3map.util import base32_ext_hex_encode, base32_ext_hex_decode, printsafe


class TestBase32ExtHex:
    def test_encode_decode_roundtrip(self):
        data = b"\x00\x01\x02\x03\x04\x05\x06\x07"
        encoded = base32_ext_hex_encode(data)
        decoded = base32_ext_hex_decode(encoded)
        assert decoded == data

    def test_encode_known_value(self):
        # SHA1 of empty wire format should produce a known encoding
        import hashlib
        h = hashlib.sha1(b"\x00").digest()
        encoded = base32_ext_hex_encode(h)
        decoded = base32_ext_hex_decode(encoded)
        assert decoded == h

    def test_decode_case_insensitive(self):
        data = b"\xde\xad\xbe\xef"
        encoded = base32_ext_hex_encode(data)
        assert base32_ext_hex_decode(encoded.lower()) == data
        assert base32_ext_hex_decode(encoded.upper()) == data

    def test_empty(self):
        assert base32_ext_hex_encode(b"") == b""
        assert base32_ext_hex_decode(b"") == b""


class TestPrintsafe:
    def test_printable_unchanged(self):
        assert printsafe("hello world") == "hello world"

    def test_control_chars_replaced(self):
        result = printsafe("hello\x00world")
        assert "\x00" not in result
        assert "\uFFFD" in result

    def test_empty(self):
        assert printsafe("") == ""
