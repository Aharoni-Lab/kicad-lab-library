"""Tests for Markdown report generation.

The report is the user-visible CI deliverable (posted as the PR
comment), and CI runs it with ``|| true`` — so a regression here would
silently ship a wrong or empty report on every PR.
"""
from __future__ import annotations

from validator.checks import CheckResult
from validator.report import generate_report


def _fail(*errors: str) -> CheckResult:
    return CheckResult(errors=list(errors))


def _ok() -> CheckResult:
    return CheckResult()


class TestOverallStatus:
    def test_all_passing_reports_pass(self):
        out = generate_report({'library-tables': _ok()})
        assert '# Validation Report: PASS' in out

    def test_any_failure_reports_fail(self):
        out = generate_report({
            'library-tables': _ok(),
            'duplicate-symbols': _fail("Duplicate symbol 'X'"),
        })
        assert '# Validation Report: FAIL' in out


class TestSymbolTable:
    def test_per_symbol_fail_attribution(self):
        """Only the symbol named in the error is marked FAIL; its
        siblings in the same file stay 'pass'."""
        path = 'symbols/AharoniLab_Test.kicad_sym'
        out = generate_report(
            {path: _fail("Symbol 'BadPart': Validated property is missing or empty")},
            symbol_names={path: ['GoodPart', 'BadPart']},
        )
        rows = {
            line.split('|')[1].strip(): line
            for line in out.splitlines() if line.startswith('| `')
        }
        assert 'FAIL' in rows['`BadPart`']
        assert 'FAIL' not in rows['`GoodPart`']

    def test_tagged_check_lands_in_its_column(self):
        path = 'symbols/AharoniLab_Test.kicad_sym'
        out = generate_report(
            {
                path: _ok(),
                f'{path} [pin-count]': _fail("Symbol 'P': has 3 pins, maximum is 2"),
            },
            symbol_names={path: ['P']},
        )
        header = next(l for l in out.splitlines() if l.startswith('| Symbol'))
        row = next(l for l in out.splitlines() if l.startswith('| `P`'))
        assert 'Pins' in header
        assert 'FAIL' in row

    def test_absolute_paths_shortened(self):
        path = '/home/runner/work/repo/symbols/AharoniLab_Test.kicad_sym'
        out = generate_report({path: _ok()}, symbol_names={path: ['P']})
        assert '/home/runner' not in out
        assert '`AharoniLab_Test`' in out


class TestFootprintTable:
    def test_footprint_rows_render(self):
        key = 'footprints/AharoniLab_Test.pretty/F1.kicad_mod [pads]'
        out = generate_report({key: _fail("Footprint 'F1': has no pads")})
        assert '## Footprints' in out
        row = next(l for l in out.splitlines() if l.startswith('| `F1`'))
        assert 'FAIL' in row


class TestErrorDetails:
    def test_errors_listed_in_details(self):
        out = generate_report({
            'symbols/AharoniLab_Test.kicad_sym [pin-count]':
                _fail("Symbol 'P': has 3 pins, maximum is 2"),
        })
        assert '<details>' in out
        assert 'has 3 pins, maximum is 2' in out
        assert 'Errors (1)' in out

    def test_no_details_section_when_clean(self):
        out = generate_report({'library-tables': _ok()})
        assert '<details>' not in out


class TestRenderPreviews:
    def test_matching_render_becomes_thumbnail(self):
        path = 'symbols/AharoniLab_Test.kicad_sym'
        out = generate_report(
            {path: _ok()},
            symbol_names={path: ['GoodPart']},
            renders_url='https://example.com/renders',
            render_files=['GoodPart_unit1.svg'],
        )
        assert '<img src="https://example.com/renders/GoodPart_unit1.svg"' in out
        assert 'GoodPart_unit1.html' in out

    def test_no_preview_column_without_renders(self):
        path = 'symbols/AharoniLab_Test.kicad_sym'
        out = generate_report({path: _ok()}, symbol_names={path: ['GoodPart']})
        assert 'Preview' not in out
