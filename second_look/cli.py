"""second-look check FILE|-  : scan a client message before you reply."""
from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap

from .model import DEFAULT_MODEL_ENV, advise
from .rules import RULES, scan, verdict

ICON = {"Stop": "STOP", "Be careful": "BE CAREFUL", "Looks OK": "LOOKS OK"}


def _wrap(s: str, indent: str = "  ") -> str:
    return textwrap.fill(s, 88, initial_indent=indent, subsequent_indent=indent)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="second-look", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check a message (file path or - for stdin)")
    c.add_argument("path")
    c.add_argument("--model", default=os.environ.get(DEFAULT_MODEL_ENV), help="path to a GGUF model")
    c.add_argument("--no-model", action="store_true", help="rules only, fixed reply")
    c.add_argument("--json", action="store_true")
    sub.add_parser("rules", help="list the rules")
    a = p.parse_args(argv)

    if a.cmd == "rules":
        for r in RULES:
            print(f"{r.id:16} {r.severity:6} {r.title.replace('*', '')}\n{_wrap(r.why, ' ' * 24)}")
        return 0

    text = sys.stdin.read() if a.path == "-" else open(a.path, encoding="utf-8").read()
    hits = scan(text)
    v = verdict(hits)
    adv = advise(text, v, hits, a.model, use_model=not a.no_model)
    if a.json:
        print(json.dumps({"verdict": v, "hits": [{"id": h.rule.id, "severity": h.rule.severity, "evidence": h.evidence} for h in hits],
                          "explanation": adv.explanation, "reply": adv.reply, "source": adv.source,
                          "meta": {k: v2 for k, v2 in adv.meta.items()}}, indent=2))
        return 0
    print(f"SECOND LOOK: {ICON[v]}")
    for h in hits:
        print(f"  [{h.rule.severity}] {h.rule.title.replace('*', '')}")
        print(f"      matched: {', '.join(repr(e) for e in h.evidence)}")
    if not hits:
        print("  no known payment-trap patterns found")
    print("\nWhy:")
    print(_wrap(adv.explanation))
    print("\nSuggested reply:")
    print(_wrap(adv.reply))
    m = adv.meta
    if adv.source == "fallback" and "model" not in m:
        note = f"fixed text, no model: {m.get('reason')}"
    else:
        note = (f"{m.get('model')}: explanation={m.get('explanation_source')}, reply={m.get('reply_source')}"
                + (f"; {m['reason']}" if m.get("reason") else ""))
    print(f"\n({note}. The verdict comes from plain rules, not the model.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
