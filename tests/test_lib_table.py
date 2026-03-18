"""Tests for the shared library table module."""
from __future__ import annotations
from pathlib import Path
from validator.lib_table import LibTableEntry, parse_lib_table, serialize_lib_table


class TestParseFromText:
    def test_parse_from_text(self):
        text = '(sym_lib_table (version 7) (lib (name "Test")(type "KiCad")(uri "/path")(options "")(descr "desc")))'
        entries = parse_lib_table(text)
        assert len(entries) == 1
        assert entries[0].name == "Test"
        assert entries[0].uri == "/path"
        assert entries[0].descr == "desc"

    def test_parse_empty_table(self):
        text = '(sym_lib_table (version 7))'
        entries = parse_lib_table(text)
        assert len(entries) == 0


class TestParseFromFilePath:
    def test_parse_from_path_object(self, tmp_path):
        table = tmp_path / "test-table"
        table.write_text('(sym_lib_table (version 7) (lib (name "A")(type "KiCad")(uri "/a")(options "")(descr "")))')
        entries = parse_lib_table(table)
        assert len(entries) == 1
        assert entries[0].name == "A"

    def test_parse_from_string_path(self, tmp_path):
        table = tmp_path / "test-table"
        table.write_text('(sym_lib_table (version 7) (lib (name "B")(type "KiCad")(uri "/b")(options "")(descr "")))')
        entries = parse_lib_table(str(table))
        assert len(entries) == 1
        assert entries[0].name == "B"


class TestToSexprFormat:
    def test_to_sexpr_format(self):
        e = LibTableEntry("Lib", "KiCad", "/path", "", "A library")
        assert '(name "Lib")' in e.to_sexpr()
        assert '(descr "A library")' in e.to_sexpr()

    def test_to_sexpr_defaults(self):
        e = LibTableEntry("X", "KiCad", "/x")
        assert '(options "")' in e.to_sexpr()
        assert '(descr "")' in e.to_sexpr()


class TestRoundtripParseSerialize:
    def test_roundtrip_parse_serialize(self):
        entries = [LibTableEntry("TestLib", "KiCad", "/path/lib.kicad_sym", "", "Test")]
        text = serialize_lib_table("sym_lib_table", entries)
        parsed = parse_lib_table(text)
        assert len(parsed) == 1
        assert parsed[0].name == "TestLib"
        assert parsed[0].uri == "/path/lib.kicad_sym"

    def test_roundtrip_via_file(self, tmp_path):
        entries = [LibTableEntry("A", "KiCad", "/a", "", "")]
        text = serialize_lib_table("fp_lib_table", entries)
        f = tmp_path / "table"
        f.write_text(text)
        parsed = parse_lib_table(f)
        assert parsed[0].name == "A"


class TestSerializeLibTable:
    def test_serialize_starts_with_kind(self):
        text = serialize_lib_table("sym_lib_table", [])
        assert text.startswith("(sym_lib_table")

    def test_serialize_includes_version(self):
        text = serialize_lib_table("sym_lib_table", [])
        assert "(version 7)" in text

    def test_serialize_ends_with_newline(self):
        text = serialize_lib_table("sym_lib_table", [])
        assert text.endswith("\n")
