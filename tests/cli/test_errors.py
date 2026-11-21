
from svgwriter.cli import main


def test_missing_file_is_one_line_error(capsys):
    assert main(["render", "does-not-exist.svg"]) == 2
    err = capsys.readouterr().err
    assert "error:" in err and "Traceback" not in err


def test_usage_errors_exit_2(capsys):
    assert main(["draw", "no-such-shape"]) == 2
    assert "no-such-shape" in capsys.readouterr().err
    assert main(["no-such-command"]) == 2


def test_no_arguments_shows_help(capsys):
    assert main([]) in (0, 2)
    assert "Commands" in capsys.readouterr().out
