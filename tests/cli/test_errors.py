from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

import svgwriter as svg
from svgwriter.cli import app, main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_missing_file_is_one_line_error(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["render", "does-not-exist.svg"]) == 2
    err = capsys.readouterr().err
    assert "error:" in err and "Traceback" not in err


def test_usage_errors_exit_2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["draw", "no-such-shape"]) == 2
    assert "no-such-shape" in capsys.readouterr().err
    assert main(["no-such-command"]) == 2
    assert main(["draw", "star", "--size", "wide"]) == 2


def test_no_arguments_shows_help(runner: CliRunner) -> None:
    result = runner.invoke(app, [])
    assert result.exit_code == 0 and "Commands:" in result.output


def test_version(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0 and result.output.strip() == f"svgwriter {svg.__version__}"


def test_every_command_has_help(runner: CliRunner) -> None:
    for name in app.list_commands(None):
        assert runner.invoke(app, [name, "--help"]).exit_code == 0


def test_draw_writes_to_a_file(runner: CliRunner, tmp_path: Path) -> None:
    target = tmp_path / "star.svg"
    assert runner.invoke(app, ["draw", "star", "--size", "50", "--compact", "-o", str(target)]).exit_code == 0
    assert target.read_text().startswith("<?xml")


class TestPresetMenu:
    @pytest.fixture(autouse=True)
    def _inside(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)

    def test_number_picks_a_preset(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(app, ["new", "talk"], input="3\n")
        assert result.exit_code == 0 and " 3. " in result.output
        assert svg.Project.load(tmp_path / "talk").config.entry == "main:slides"

    def test_enter_takes_the_first(self, runner: CliRunner, tmp_path: Path) -> None:
        assert runner.invoke(app, ["new", "first"], input="\n").exit_code == 0
        assert (tmp_path / "first" / "svgwriter.toml").is_file()

    def test_out_of_range_asks_again(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["new", "again"], input="99\n1\n")
        assert result.exit_code == 0 and "not in the range" in result.output
