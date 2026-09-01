"""Tests for the CLI entry point (``python -m validator``).

CI invokes ``main()`` directly for gating and report generation, so its
exit codes and output are load-bearing: a wiring bug here would neuter
the real merge gate while the rest of the suite stays green.
"""
from __future__ import annotations

from conftest import GOOD_SYMBOL_PROPS, make_symbol, make_symbol_lib
from validator.__main__ import main


class TestExitCodes:
    def test_clean_repo_exits_0(self, tmp_repo, monkeypatch, capsys):
        monkeypatch.chdir(tmp_repo)
        rc = main(['--all', '--check-tables', '--check-generated-tables'])
        out = capsys.readouterr().out
        assert rc == 0
        assert 'FAIL' not in out
        assert 'PASS' in out

    def test_failing_symbol_exits_1(self, tmp_repo, monkeypatch, capsys):
        bad_props = dict(GOOD_SYMBOL_PROPS)
        del bad_props['Validated']
        (tmp_repo / 'symbols' / 'AharoniLab_Test.kicad_sym').write_text(
            make_symbol_lib(make_symbol('BadPart', bad_props))
        )
        monkeypatch.chdir(tmp_repo)
        rc = main(['--all'])
        out = capsys.readouterr().out
        assert rc == 1
        assert 'FAIL' in out
        assert 'Validated' in out

    def test_parse_error_exits_1(self, tmp_repo, monkeypatch, capsys):
        broken = tmp_repo / 'symbols' / 'AharoniLab_Test.kicad_sym'
        broken.write_text('(kicad_symbol_lib (symbol "Unclosed"')
        monkeypatch.chdir(tmp_repo)
        rc = main([str(broken)])
        out = capsys.readouterr().out
        assert rc == 1
        assert 'FAIL' in out

    def test_duplicate_symbols_fail_check_all(self, tmp_repo, monkeypatch, capsys):
        lib = make_symbol_lib(make_symbol('GoodPart', GOOD_SYMBOL_PROPS))
        (tmp_repo / 'symbols' / 'AharoniLab_Test.kicad_sym').write_text(lib)
        (tmp_repo / 'symbols' / 'AharoniLab_Other.kicad_sym').write_text(lib)
        monkeypatch.chdir(tmp_repo)
        rc = main(['--all'])
        out = capsys.readouterr().out
        assert rc == 1
        assert 'Duplicate' in out

    def test_stale_tables_fail_generated_check(self, tmp_repo, monkeypatch, capsys):
        (tmp_repo / 'sym-lib-table').write_text('(sym_lib_table (version 7))')
        monkeypatch.chdir(tmp_repo)
        rc = main(['--check-generated-tables'])
        out = capsys.readouterr().out
        assert rc == 1
        assert 'does not match generated' in out


class TestReportMode:
    def test_report_outputs_markdown(self, tmp_repo, monkeypatch, capsys):
        monkeypatch.chdir(tmp_repo)
        rc = main(['--report', '--all'])
        out = capsys.readouterr().out
        assert rc == 0
        assert '# Validation Report: PASS' in out
        assert '`GoodPart`' in out
        assert '## Structure' in out

    def test_report_shows_failures(self, tmp_repo, monkeypatch, capsys):
        bad_props = dict(GOOD_SYMBOL_PROPS)
        del bad_props['Validated']
        (tmp_repo / 'symbols' / 'AharoniLab_Test.kicad_sym').write_text(
            make_symbol_lib(make_symbol('BadPart', bad_props))
        )
        monkeypatch.chdir(tmp_repo)
        rc = main(['--report', '--all'])
        out = capsys.readouterr().out
        assert rc == 1
        assert '# Validation Report: FAIL' in out
        assert 'Validated' in out

    def test_report_is_quiet_apart_from_markdown(self, tmp_repo, monkeypatch, capsys):
        """--report must not interleave PASS/FAIL console lines with the
        Markdown (CI pipes stdout straight into the PR comment)."""
        monkeypatch.chdir(tmp_repo)
        main(['--report', '--all'])
        out = capsys.readouterr().out
        assert 'PASS:' not in out


class TestFootprintFiles:
    def test_padless_footprint_fails(self, tmp_repo, monkeypatch, capsys):
        fp_dir = tmp_repo / 'footprints' / 'AharoniLab_Test.pretty'
        fp_dir.mkdir(parents=True)
        fp_file = fp_dir / 'NoPads.kicad_mod'
        fp_file.write_text('(footprint "NoPads" (layer "F.Cu"))')
        monkeypatch.chdir(tmp_repo)
        rc = main(['--footprint-files', str(fp_file)])
        out = capsys.readouterr().out
        assert rc == 1
        assert 'no pads' in out
