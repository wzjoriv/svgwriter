from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from click.testing import CliRunner

import svgwriter as svg
from svgwriter.tools.cli import _project as project_commands
from svgwriter.tools.cli import app, main
from svgwriter.tools.cli._constants import CUSTOM_SIZE, KEEP_CHOICE
from svgwriter.tools.cli._prompts import parse_size

WIDTH = "Width (a number or a length such as 50cm)"


class Answer:
    def __init__(self, value: object) -> None:
        self.value = value

    def ask(self) -> object:
        return self.value


class FakeQuestionary(types.ModuleType):
    """Stands in for questionary: answers each prompt by its message and records what was asked."""

    def __init__(self, answers: dict[str, object]) -> None:
        super().__init__("questionary")
        self.answers = answers
        self.asked: list[str] = []

    def Choice(self, title: str, value: object) -> tuple[str, object]:
        return title, value

    def select(self, message: str, choices: list[tuple[str, object]]) -> Answer:
        self.asked.append(message)
        assert self.answers[message] in [value for _, value in choices]
        return Answer(self.answers[message])

    def text(self, message: str, validate: object = None) -> Answer:
        self.asked.append(message)
        return Answer(self.answers[message])


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _inside(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


def terminal(monkeypatch: pytest.MonkeyPatch, *, questionary: FakeQuestionary | None = None) -> None:
    monkeypatch.setattr(project_commands, "interactive", lambda: True)
    monkeypatch.setattr(project_commands, "has_questionary", lambda: questionary is not None)
    if questionary is not None:
        monkeypatch.setitem(sys.modules, "questionary", questionary)


def sides(path: Path) -> list[str]:
    return [str(side) for side in svg.Project.load(path).config.size]


class TestArrowKeyPrompts:
    def test_every_missing_choice_is_asked(self, runner: CliRunner, tmp_path: Path,
                                           monkeypatch: pytest.MonkeyPatch) -> None:
        fake = FakeQuestionary({"Project name": "deck", "Preset": "slides", "Drawing in a": True,
                                "Theme": "dracula", "Page size": "a4"})
        terminal(monkeypatch, questionary=fake)
        result = runner.invoke(app, ["new"])
        assert result.exit_code == 0, result.output
        assert fake.asked == ["Project name", "Preset", "Drawing in a", "Theme", "Page size"]
        project = svg.Project.load(tmp_path / "deck")
        assert project.config.entry == "main.ipynb:slides" and project.config.size == "a4"
        assert 'extends = "dracula"' in (tmp_path / "deck" / "theme.toml").read_text(encoding="utf-8")

    def test_flags_skip_their_prompts(self, runner: CliRunner, tmp_path: Path,
                                      monkeypatch: pytest.MonkeyPatch) -> None:
        fake = FakeQuestionary({})
        terminal(monkeypatch, questionary=fake)
        result = runner.invoke(app, ["new", "poster", "--preset", "poster", "--script", "--theme", "noir",
                                     "--size", "a3"])
        assert result.exit_code == 0 and fake.asked == []
        assert svg.Project.load(tmp_path / "poster").config.size == "a3"

    def test_keeping_the_presets_own_changes_nothing(self, runner: CliRunner, tmp_path: Path,
                                                     monkeypatch: pytest.MonkeyPatch) -> None:
        fake = FakeQuestionary({"Preset": "poster", "Drawing in a": False, "Theme": KEEP_CHOICE, "Page size": KEEP_CHOICE})
        terminal(monkeypatch, questionary=fake)
        assert runner.invoke(app, ["new", "kept"]).exit_code == 0
        assert svg.Project.load(tmp_path / "kept").config.size == "a4"
        assert 'extends = "print"' in (tmp_path / "kept" / "theme.toml").read_text(encoding="utf-8")

    def test_custom_size_asks_width_and_height(self, runner: CliRunner, tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
        fake = FakeQuestionary({"Preset": "blank", "Drawing in a": False, "Theme": KEEP_CHOICE, "Page size": CUSTOM_SIZE,
                                WIDTH: "50cm", "Height": "70"})
        terminal(monkeypatch, questionary=fake)
        assert runner.invoke(app, ["new", "wide"]).exit_code == 0
        assert sides(tmp_path / "wide") == ["50cm", "70"]

    def test_cancelling_aborts(self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        terminal(monkeypatch, questionary=FakeQuestionary({"Preset": None}))
        assert runner.invoke(app, ["new", "gone"]).exit_code == 1
        assert not (tmp_path / "gone").exists()


class TestNumberedMenu:
    def test_number_picks_a_preset(self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        terminal(monkeypatch)
        result = runner.invoke(app, ["new", "talk"], input="3\n")
        assert result.exit_code == 0 and " 3. " in result.output
        assert svg.Project.load(tmp_path / "talk").config.entry == "main:slides"

    def test_enter_takes_the_first(self, runner: CliRunner, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        terminal(monkeypatch)
        assert runner.invoke(app, ["new", "first"], input="\n").exit_code == 0
        assert (tmp_path / "first" / "svgwriter.toml").is_file()

    def test_out_of_range_asks_again(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        terminal(monkeypatch)
        result = runner.invoke(app, ["new", "again"], input="99\n1\n")
        assert result.exit_code == 0 and "not in the range" in result.output

    def test_name_is_asked_when_missing(self, runner: CliRunner, tmp_path: Path,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
        terminal(monkeypatch)
        assert runner.invoke(app, ["new", "--preset", "blank"], input="named\n").exit_code == 0
        assert (tmp_path / "named").is_dir()

    def test_flags_apply_without_questionary(self, runner: CliRunner, tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch) -> None:
        terminal(monkeypatch)
        result = runner.invoke(app, ["new", "flagged", "--preset", "blank", "--size", "800,50cm", "--theme", "mono"])
        assert result.exit_code == 0
        assert sides(tmp_path / "flagged") == ["800", "50cm"]


class TestWithoutATerminal:
    def test_defaults_and_no_prompt(self, runner: CliRunner, tmp_path: Path) -> None:
        result = runner.invoke(app, ["new", "quiet"], input="3\n")
        assert result.exit_code == 0 and "Preset" not in result.output
        assert svg.Project.load(tmp_path / "quiet").config.entry == "main:build"

    def test_missing_name_is_an_error(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["new"])
        assert result.exit_code == 2 and "missing argument NAME" in result.output

    @pytest.mark.parametrize(("flags", "message"), [(["--theme", "nope"], "unknown theme"),
                                                    (["--size", "nope"], "unknown size")])
    def test_bad_choices_fail_clearly(self, tmp_path: Path, capsys: pytest.CaptureFixture[str], flags: list[str],
                                      message: str) -> None:
        assert main(["new", "bad", *flags]) == 2
        assert message in capsys.readouterr().err and not (tmp_path / "bad").exists()


def test_parse_size() -> None:
    assert parse_size("a4") == "a4"
    assert parse_size("800, 50cm") == [800.0, "50cm"]
    with pytest.raises(ValueError):
        parse_size("wide,tall")
