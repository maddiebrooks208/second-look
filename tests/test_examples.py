import json
from pathlib import Path

import pytest

from second_look.rules import scan, verdict

EX = Path(__file__).resolve().parent.parent / "examples"
EXPECTED = json.loads((EX / "expected.json").read_text())


def test_every_example_has_an_expectation():
    assert sorted(p.stem for p in EX.glob("*.txt")) == sorted(EXPECTED)
    assert len(EXPECTED) >= 20


@pytest.mark.parametrize("name", sorted(EXPECTED))
def test_example(name):
    want_verdict, want_ids = EXPECTED[name]
    hits = scan((EX / f"{name}.txt").read_text())
    assert sorted(h.rule.id for h in hits) == sorted(want_ids)
    assert verdict(hits) == want_verdict
