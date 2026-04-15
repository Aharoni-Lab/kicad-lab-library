"""Shared library table parsing and serialization for KiCad library tables."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from validator.sexpr import parse_sexpr


@dataclass
class LibTableEntry:
    """A single entry from a KiCad library table file."""
    name: str
    type: str
    uri: str
    options: str = ""
    descr: str = ""

    def to_sexpr(self) -> str:
        return (
            f'  (lib (name "{self.name}")(type "{self.type}")'
            f'(uri "{self.uri}")(options "{self.options}")'
            f'(descr "{self.descr}"))'
        )


def parse_lib_table(source: str | Path) -> List[LibTableEntry]:
    """Parse a KiCad library table. Accepts file path (Path) or text content (str)."""
    if isinstance(source, Path):
        text = source.read_text(encoding='utf-8')
    elif isinstance(source, str) and source.lstrip().startswith('('):
        text = source
    else:
        path = Path(source)
        if path.is_file():
            text = path.read_text(encoding='utf-8')
        else:
            text = source

    tree = parse_sexpr(text)
    entries: List[LibTableEntry] = []
    for node in tree:
        if not isinstance(node, list) or node[0] != 'lib':
            continue
        fields: Dict[str, str] = {}
        for child in node[1:]:
            if isinstance(child, list) and len(child) == 2:
                fields[child[0]] = child[1]
        entries.append(LibTableEntry(
            name=fields.get('name', ''),
            type=fields.get('type', ''),
            uri=fields.get('uri', ''),
            options=fields.get('options', ''),
            descr=fields.get('descr', ''),
        ))
    return entries


def serialize_lib_table(kind: str, entries: List[LibTableEntry]) -> str:
    """Serialize a list of LibTableEntry objects into a KiCad table file."""
    lines = [f"({kind}", "  (version 7)"]
    for entry in entries:
        lines.append(entry.to_sexpr())
    lines.append(")")
    return "\n".join(lines) + "\n"
