"""Shared S-expression parser for KiCad files.

KiCad files (.kicad_sym, .kicad_mod, library tables) use S-expressions:
nested parenthesised structures like ``(keyword args... (children...))``.

This module provides a single ``parse_sexpr()`` function used by both
``validate.py`` and ``install.py``.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Token kinds. Atoms carry their (unescaped) text; parens carry None.
# Keeping the kind separate means a quoted value of "(" or ")" can never
# be mistaken for a structural parenthesis.
_OPEN = 'open'
_CLOSE = 'close'
_ATOM = 'atom'

_Token = Tuple[str, str]


def parse_sexpr(text: str) -> list:
    """Parse a KiCad S-expression string into a nested list structure.

    Quoted strings (including escaped quotes) and unquoted tokens are
    both supported.  Returns a nested list where each ``(...)`` group
    becomes a Python list whose first element is the keyword token.

    Raises :class:`ValueError` on unbalanced parentheses, unterminated
    strings, or empty input.
    """
    tokens = _tokenize(text)
    if not tokens:
        raise ValueError("Empty S-expression")
    open_count = sum(1 for kind, _ in tokens if kind == _OPEN)
    close_count = sum(1 for kind, _ in tokens if kind == _CLOSE)
    if open_count != close_count:
        raise ValueError(
            f"Malformed S-expression: unbalanced parentheses "
            f"({open_count} open, {close_count} close)"
        )
    result, _ = _parse_tokens(tokens, 0)
    # If top-level produced a single group, return it directly.
    if len(result) == 1:
        return result[0]
    return result


def _tokenize(text: str) -> List[_Token]:
    """Tokenize an S-expression string into ``(kind, value)`` tuples.

    Kinds are ``open``, ``close``, and ``atom`` (quoted-string contents,
    unescaped, or bare words).  Raises :class:`ValueError` on a quoted
    string with no closing quote.
    """
    tokens: List[_Token] = []
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]

        # Skip whitespace
        if ch in (' ', '\t', '\n', '\r'):
            i += 1
            continue

        # Open / close parens
        if ch == '(':
            tokens.append((_OPEN, ''))
            i += 1
            continue
        if ch == ')':
            tokens.append((_CLOSE, ''))
            i += 1
            continue

        # Quoted string
        if ch == '"':
            j = i + 1
            while j < length:
                if text[j] == '\\':
                    j += 2  # skip escaped character
                    continue
                if text[j] == '"':
                    break
                j += 1
            if j >= length:
                raise ValueError(
                    f"Unterminated quoted string starting at offset {i}"
                )
            # Extract content between quotes (unescaping inner quotes)
            raw = text[i + 1 : j]
            unescaped = raw.replace('\\\\', '\x00').replace('\\"', '"').replace('\x00', '\\')
            tokens.append((_ATOM, unescaped))
            i = j + 1
            continue

        # Bare token (unquoted)
        j = i
        while j < length and text[j] not in ('(', ')', ' ', '\t', '\n', '\r', '"'):
            j += 1
        tokens.append((_ATOM, text[i:j]))
        i = j

    return tokens


def extract_properties(sexpr_node: list) -> Dict[str, str]:
    """Return a dict of property name -> value from an S-expression node.

    Works for both symbol and footprint nodes — any node containing
    ``(property "name" "value" ...)`` children.
    """
    props: Dict[str, str] = {}
    for child in sexpr_node:
        if isinstance(child, list) and len(child) >= 3 and child[0] == 'property':
            props[child[1]] = child[2]
    return props


def _parse_tokens(tokens: List[_Token], pos: int) -> tuple:
    """Recursively parse tokens starting at *pos*.

    Returns ``(result_list, new_pos)``.
    """
    result: list = []
    while pos < len(tokens):
        kind, value = tokens[pos]
        if kind == _OPEN:
            child, pos = _parse_tokens(tokens, pos + 1)
            result.append(child)
        elif kind == _CLOSE:
            return result, pos + 1
        else:
            result.append(value)
            pos += 1
    return result, pos
