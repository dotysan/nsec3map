"""Tests for n3map.rrtypes — RR, NSEC, and NSEC3 record parsing."""

import pytest

from n3map.rrtypes import rr, nsec, nsec3
from n3map.exception import ParseError, NSEC3Error


class TestRRParser:
    """Tests for the general RR text parser."""

    def setup_method(self):
        self.parse = rr.parser()

    def test_parse_basic_rr(self):
        result = self.parse("example.com.\t300\tIN\tNSEC foo.example.com. A NS")
        assert result is not None
        owner, ttl, cls, rest = result
        assert str(owner) == "example.com."
        assert ttl == 300
        assert cls == "IN"
        assert "NSEC" in rest

    def test_parse_root(self):
        result = self.parse(".\t86400\tIN\tNSEC a. NS SOA")
        assert result is not None
        owner, ttl, cls, rest = result
        assert str(owner) == "."
        assert ttl == 86400

    def test_returns_none_for_garbage(self):
        assert self.parse("not a record") is None

    def test_returns_none_for_empty(self):
        assert self.parse("") is None

    def test_non_in_class_returns_none(self):
        # Parser only matches IN class
        assert self.parse("example.com.\t300\tCH\tNSEC foo.") is None


class TestNSECParser:
    """Tests for NSEC record parsing."""

    def setup_method(self):
        self.parse = nsec.parser()

    def test_parse_basic_nsec(self):
        line = "alpha.example.com.\t300\tIN\tNSEC beta.example.com. A NS SOA"
        result = self.parse(line)
        assert result is not None
        assert str(result.owner) == "alpha.example.com."
        assert str(result.next_owner) == "beta.example.com."
        assert "A" in result.types
        assert "NS" in result.types

    def test_returns_none_for_non_nsec(self):
        line = "example.com.\t300\tIN\tA 1.2.3.4"
        assert self.parse(line) is None

    def test_returns_none_for_garbage(self):
        assert self.parse("garbage") is None


class TestNSEC3Parser:
    """Tests for NSEC3 record parsing."""

    def setup_method(self):
        self.parse = nsec3.parser()

    def test_parse_basic_nsec3(self):
        # Build a valid NSEC3 record text line
        # Hash is 32-char base32hex, next hash is 32-char base32hex
        line = (
            "04sknapca5al7qos3km2l9tl3p5okq4c.example.com.\t300\tIN\t"
            "NSEC3 1 0 10 aabbccdd 04sknapca5al7qos3km2l9tl3p5okq4c A NS SOA"
        )
        result = self.parse(line)
        assert result is not None
        assert result.algorithm == 1
        assert result.flags == 0
        assert result.iterations == 10
        assert result.salt == bytes.fromhex("aabbccdd")
        assert "A" in result.types

    def test_parse_empty_salt(self):
        line = (
            "04sknapca5al7qos3km2l9tl3p5okq4c.example.com.\t300\tIN\t"
            "NSEC3 1 0 10 - 04sknapca5al7qos3km2l9tl3p5okq4c A NS"
        )
        result = self.parse(line)
        assert result is not None
        assert result.salt == b""

    def test_returns_none_for_garbage(self):
        assert self.parse("garbage") is None


class TestNSEC3ComputeHash:
    """Tests for NSEC3 hash computation (RFC 5155)."""

    def test_hash_returns_20_bytes(self):
        from n3map.name import domainname_from_text
        dn = domainname_from_text("example.com.")
        h = nsec3.compute_hash(dn, salt=b"", iterations=0)
        assert len(h) == 20

    def test_hash_deterministic(self):
        from n3map.name import domainname_from_text
        dn = domainname_from_text("example.com.")
        h1 = nsec3.compute_hash(dn, salt=b"\xaa\xbb", iterations=5)
        h2 = nsec3.compute_hash(dn, salt=b"\xaa\xbb", iterations=5)
        assert h1 == h2

    def test_different_salt_different_hash(self):
        from n3map.name import domainname_from_text
        dn = domainname_from_text("example.com.")
        h1 = nsec3.compute_hash(dn, salt=b"\x00", iterations=0)
        h2 = nsec3.compute_hash(dn, salt=b"\xff", iterations=0)
        assert h1 != h2

    def test_unknown_algorithm_raises(self):
        from n3map.name import domainname_from_text
        dn = domainname_from_text("example.com.")
        with pytest.raises(NSEC3Error):
            nsec3.compute_hash(dn, salt=b"", iterations=0, algorithm=0)


class TestNSEC3Interval:
    """Tests for NSEC3 interval coverage checks."""

    def test_normal_interval(self):
        lo = b"\x00" * 20
        hi = b"\xff" * 20
        mid = b"\x80" + b"\x00" * 19
        assert nsec3.covered_by_nsec3_interval(mid, lo, hi) is True

    def test_outside_interval(self):
        lo = b"\x10" + b"\x00" * 19
        hi = b"\x20" + b"\x00" * 19
        outside = b"\x30" + b"\x00" * 19
        assert nsec3.covered_by_nsec3_interval(outside, lo, hi) is False

    def test_wraparound_interval(self):
        # Last record: owner > next_owner (wraps around)
        lo = b"\xf0" + b"\x00" * 19
        hi = b"\x10" + b"\x00" * 19
        inside = b"\xff" + b"\x00" * 19
        assert nsec3.covered_by_nsec3_interval(inside, lo, hi) is True

    def test_wraparound_low_side(self):
        lo = b"\xf0" + b"\x00" * 19
        hi = b"\x10" + b"\x00" * 19
        inside = b"\x05" + b"\x00" * 19
        assert nsec3.covered_by_nsec3_interval(inside, lo, hi) is True

    def test_distance_covered_normal(self):
        lo = b"\x00" * 20
        hi = b"\x00" * 19 + b"\x0a"
        assert nsec3.distance_covered(lo, hi) == 10

    def test_distance_covered_same_is_max(self):
        h = b"\xab" * 20
        assert nsec3.distance_covered(h, h) == nsec3.SHA1_MAX
