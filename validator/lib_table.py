"""Shared library table parsing and serialization for KiCad library tables."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from validator.sexpr import parse_sexpr

# The standard per-entry fields this module models explicitly. Anything
# else KiCad writes (e.g. a bare "(disabled)" on deactivated libraries)
# is preserved verbatim in ``LibTableEntry.extras``.
_KNOWN_FIELDS = ('name', 'type', 'uri', 'options', 'descr')


def _escape(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


def _node_to_sexpr(node) -> str:
    """Serialize a parsed child node back to text.

    Follows KiCad's table format: the leading keyword is bare, values
    are quoted strings.
    """
    if not isinstance(node, list):
        return f'"{_escape(node)}"'
    if not node:
        return '()'
    parts = [str(node[0])]
    parts.extend(_node_to_sexpr(child) for child in node[1:])
    return '(' + ' '.join(parts) + ')'


@dataclass
class LibTableEntry:
    """A single entry from a KiCad library table file."""
    name: str
    type: str
    uri: str
    options: str = ""
    descr: str = ""
    # Child nodes beyond the standard fields — e.g. (disabled), (hidden) —
    # round-tripped so rewriting a user's global table never drops them.
    extras: List[list] = field(default_factory=list)

    def to_sexpr(self) -> str:
        text = (
            f'  (lib (name "{_escape(self.name)}")(type "{_escape(self.type)}")'
            f'(uri "{_escape(self.uri)}")(options "{_escape(self.options)}")'
            f'(descr "{_escape(self.descr)}")'
        )
        for extra in self.extras:
            text += _node_to_sexpr(extra)
        return text + ')'


def parse_lib_table(source: str | Path) -> List[LibTableEntry]:
    """Parse a KiCad library table. Accepts a file path (Path) or text content (str).

    A string that does not look like table text is treated as a path and
    must exist — a missing file raises ``ValueError`` instead of silently
    parsing as an empty table.
    """
    if isinstance(source, Path):
        text = source.read_text(encoding='utf-8')
    elif source.lstrip().startswith('('):
        text = source
    else:
        path = Path(source)
        if not path.is_file():
            raise ValueError(f"Library table not found: {source}")
        text = path.read_text(encoding='utf-8')

    tree = parse_sexpr(text)
    entries: List[LibTableEntry] = []
    for node in tree:
        if not isinstance(node, list) or not node or node[0] != 'lib':
            continue
        fields: Dict[str, str] = {}
        extras: List[list] = []
        for child in node[1:]:
            if (
                isinstance(child, list) and len(child) == 2
                and child[0] in _KNOWN_FIELDS
            ):
                fields[child[0]] = child[1]
            else:
                extras.append(child)
        entries.append(LibTableEntry(
            name=fields.get('name', ''),
            type=fields.get('type', ''),
            uri=fields.get('uri', ''),
            options=fields.get('options', ''),
            descr=fields.get('descr', ''),
            extras=extras,
        ))
    return entries


def serialize_lib_table(kind: str, entries: List[LibTableEntry]) -> str:
    """Serialize a list of LibTableEntry objects into a KiCad table file."""
    lines = [f"({kind}", "  (version 7)"]
    for entry in entries:
        lines.append(entry.to_sexpr())
    lines.append(")")
    return "\n".join(lines) + "\n"
