"""Tests for the shared S-expression parser.

These tests ensure:
- Valid S-expressions parse into correct nested structures
- Quoted strings (including escaped quotes) are handled
- Unbalanced parentheses produce clear errors
- Empty input is rejected
"""
from __future__ import annotations

import pytest

from validator.sexpr import parse_sexpr


class TestBasicParsing:
    def test_simple_nested(self):
        """Simple nested S-expression should produce correct list structure."""
        result = parse_sexpr('(foo (bar "baz"))')
        assert result == ['foo', ['bar', 'baz']]

    def test_bare_tokens(self):
        """Bare (unquoted) tokens should be returned as strings."""
        result = parse_sexpr('(version 7)')
        assert result == ['version', '7']

    def test_multiple_children(self):
        """Multiple child groups at the same level."""
        result = parse_sexpr('(root (a 1) (b 2))')
        assert result == ['root', ['a', '1'], ['b', '2']]

    def test_deeply_nested(self):
        """Deeply nested structures should parse correctly."""
        result = parse_sexpr('(a (b (c "deep")))')
        assert result == ['a', ['b', ['c', 'deep']]]


class TestQuotedStrings:
    def test_quoted_string_value(self):
        """Quoted string contents should be extracted without quotes."""
        result = parse_sexpr('(name "hello world")')
        assert result == ['name', 'hello world']

    def test_escaped_quotes(self):
        """Escaped quotes inside strings should be unescaped."""
        result = parse_sexpr(r'(name "say \"hi\"")')
        assert result == ['name', 'say "hi"']

    def test_empty_quoted_string(self):
        """Empty quoted string should produce empty string token."""
        result = parse_sexpr('(value "")')
        assert result == ['value', '']


class TestErrorHandling:
    def test_unbalanced_open(self):
        """Unbalanced open parenthesis should raise ValueError."""
        with pytest.raises(ValueError, match="unbalanced"):
            parse_sexpr('(foo (bar)')

    def test_unbalanced_close(self):
        """Unbalanced close parenthesis should raise ValueError."""
        with pytest.raises(ValueError, match="unbalanced"):
            parse_sexpr('(foo) )')

    def test_empty_input(self):
        """Empty input should raise ValueError."""
        with pytest.raises(ValueError, match="Empty"):
            parse_sexpr('')

    def test_whitespace_only(self):
        """Whitespace-only input should raise ValueError."""
        with pytest.raises(ValueError, match="Empty"):
            parse_sexpr('   \n\t  ')


class TestEscapeHandling:
    def test_escaped_backslash(self):
        result = parse_sexpr(r'(path "C:\\Users\\foo")')
        assert result == ['path', 'C:\\Users\\foo']

    def test_escaped_backslash_before_quote(self):
        result = parse_sexpr(r'(val "end\\\"")')
        assert result == ['val', 'end\\"']

    def test_backslash_at_end(self):
        result = parse_sexpr(r'(val "trailing\\")')
        assert result == ['val', 'trailing\\']


class TestKicadFormats:
    def test_library_table(self):
        """Should parse a minimal KiCad library table."""
        text = """(sym_lib_table
  (version 7)
  (lib (name "TestLib")(type "KiCad")(uri "/path/to/lib")(options "")(descr "Test"))
)"""
        result = parse_sexpr(text)
        assert result[0] == 'sym_lib_table'
        assert result[1] == ['version', '7']
        assert result[2][0] == 'lib'

    def test_symbol_file(self):
        """Should parse a minimal KiCad symbol structure."""
        text = """(kicad_symbol_lib
  (version 20241209)
  (symbol "R"
    (property "Reference" "R")
    (property "Value" "R")
  )
)"""
        result = parse_sexpr(text)
        assert result[0] == 'kicad_symbol_lib'
        # Find the symbol node
        symbol = [n for n in result if isinstance(n, list) and n[0] == 'symbol'][0]
        assert symbol[1] == 'R'
