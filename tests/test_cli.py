import json
from pathlib import Path

from second_look.cli import main

EX = Path(__file__).resolve().parent.parent / "examples"


def test_cli_json_no_model(capsys):
    assert main(["check", str(EX / "01-reverse-invoice-paypal.txt"), "--no-model", "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "Stop" and out["source"] == "fallback"
    assert out["hits"][0]["id"] == "reverse-invoice"


def test_cli_text(capsys):
    main(["check", str(EX / "12-legit-candles.txt"), "--no-model"])
    out = capsys.readouterr().out
    assert "LOOKS OK" in out and "Suggested reply" in out


def test_cli_rules(capsys):
    main(["rules"])
    assert "reverse-invoice" in capsys.readouterr().out
