import pytest

from svgwriter.cli import main


def test_missing_file_is_one_line_error(capsys):
    with pytest.raises(SystemExit) as raised:
        main(["render", "does-not-exist.svg"])
    assert raised.value.code == 2
    err = capsys.readouterr().err
    assert "error:" in err and "Traceback" not in err
