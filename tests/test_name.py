"""Tests for n3map.name — Label, DomainName, and wire format."""

import pytest

from n3map.name import (
    Label, DomainName, domainname_from_text, fqdn_from_text,
    domainname_from_wire, unvis_domainname, label_generator, hex_label,
    _label_ldh, _label_binary,
)
from n3map.exception import (
    InvalidDomainNameError, MaxLabelLengthError, MaxLabelValueError,
    MaxDomainNameLengthError,
)


class TestLabel:
    def test_create(self):
        lbl = Label(b"example")
        assert lbl.label == b"example"

    def test_canonicalize_lowercase(self):
        lbl = Label(b"EXAMPLE")
        assert lbl.label == b"example"

    def test_max_length_ok(self):
        Label(b"a" * 63)

    def test_exceeds_max_length(self):
        with pytest.raises(MaxLabelLengthError):
            Label(b"a" * 64)

    def test_ordering(self):
        a = Label(b"alpha")
        b = Label(b"beta")
        assert a < b
        assert not b < a

    def test_equality(self):
        assert Label(b"test") == Label(b"TEST")

    def test_to_wire(self):
        lbl = Label(b"abc")
        assert lbl.to_wire() == b"\x03abc"

    def test_wire_length(self):
        lbl = Label(b"abc")
        assert lbl.wire_length() == 4  # 1 length byte + 3

    def test_forward_next_binary(self):
        lbl = Label(b"\x00")
        nxt = lbl.forward_next_binary(extend=False)
        assert nxt.label == b"\x01"

    def test_forward_next_binary_extend(self):
        lbl = Label(b"\x00")
        nxt = lbl.forward_next_binary(extend=True)
        assert nxt.label == b"\x00\x00"

    def test_forward_next_ldh(self):
        lbl = Label(b"a")
        nxt = lbl.forward_next_ldh(extend=False)
        assert nxt.label == b"b"

    def test_has_max_value_binary(self):
        lbl = Label(b"\xff")
        assert lbl.has_max_value(ldh=False) is True

    def test_has_max_value_binary_false(self):
        lbl = Label(b"\x00")
        assert lbl.has_max_value(ldh=False) is False

    def test_max_value_binary_raises(self):
        lbl = Label(b"\xff")
        with pytest.raises(MaxLabelValueError):
            lbl.forward_next_binary(extend=False)


class TestDomainName:
    def test_create(self):
        dn = DomainName(Label(b"example"), Label(b"com"), Label(b""))
        assert str(dn) == "example.com."

    def test_root(self):
        dn = DomainName(Label(b""))
        assert dn.is_root()
        assert str(dn) == "."

    def test_num_labels(self):
        dn = DomainName(Label(b"a"), Label(b"b"), Label(b""))
        assert dn.num_labels() == 3

    def test_part_of_zone(self):
        zone = domainname_from_text("example.com.")
        sub = domainname_from_text("www.example.com.")
        assert sub.part_of_zone(zone)

    def test_not_part_of_zone(self):
        zone = domainname_from_text("example.com.")
        other = domainname_from_text("example.org.")
        assert not other.part_of_zone(zone)

    def test_ordering(self):
        a = domainname_from_text("a.example.com.")
        b = domainname_from_text("b.example.com.")
        assert a < b

    def test_equality(self):
        a = domainname_from_text("example.com.")
        b = domainname_from_text("EXAMPLE.COM.")
        assert a == b

    def test_to_wire(self):
        dn = domainname_from_text("a.b.")
        wire = dn.to_wire()
        assert wire == b"\x01a\x01b\x00"

    def test_split(self):
        dn = domainname_from_text("www.example.com.")
        first, second = dn.split(1)
        assert str(first) == "www"
        assert str(second) == "example.com."

    def test_next_label_add_binary(self):
        dn = domainname_from_text("example.com.")
        new = dn.next_label_add(ldh=False)
        assert new.num_labels() == dn.num_labels() + 1

    def test_next_label_add_ldh(self):
        dn = domainname_from_text("example.com.")
        new = dn.next_label_add(ldh=True)
        assert new.num_labels() == dn.num_labels() + 1

    def test_covered_by_normal(self):
        owner = domainname_from_text("a.example.com.")
        nxt = domainname_from_text("c.example.com.")
        mid = domainname_from_text("b.example.com.")
        assert mid.covered_by(owner, nxt)

    def test_covered_by_wraparound(self):
        owner = domainname_from_text("z.example.com.")
        nxt = domainname_from_text("a.example.com.")
        after = domainname_from_text("zz.example.com.")
        assert after.covered_by(owner, nxt)

    def test_no_labels_raises(self):
        with pytest.raises(InvalidDomainNameError):
            DomainName()


class TestDomainNameFromText:
    def test_fqdn(self):
        dn = domainname_from_text("example.com.")
        assert str(dn) == "example.com."

    def test_fqdn_from_text_appends_dot(self):
        dn = fqdn_from_text("example.com")
        assert str(dn) == "example.com."

    def test_fqdn_from_text_already_fqdn(self):
        dn = fqdn_from_text("example.com.")
        assert str(dn) == "example.com."


class TestDomainNameFromWire:
    def test_roundtrip(self):
        dn = domainname_from_text("www.example.com.")
        wire = dn.to_wire()
        dn2 = domainname_from_wire(wire)
        assert dn == dn2


class TestHexLabel:
    def test_zero(self):
        assert hex_label(0) == b"0"

    def test_positive(self):
        assert hex_label(255) == b"ff"


class TestLabelGenerator:
    def test_generates_sequence(self):
        gen = label_generator(hex_label, init=0)
        lbl0, i0 = next(gen)
        lbl1, i1 = next(gen)
        assert i0 == 0
        assert i1 == 1
        assert lbl0.label == b"0"
        assert lbl1.label == b"1"
