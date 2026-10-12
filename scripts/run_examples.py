"""Run every example through rules + local model and write logs/run-<date>.jsonl and a summary."""
import datetime as dt, json, os, platform, sys, time
from pathlib import Path
from second_look.model import advise
from second_look.rules import scan, verdict

root = Path(__file__).resolve().parent.parent
model = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("SECOND_LOOK_MODEL")
stamp = dt.datetime.now().astimezone()
out = root / "logs" / f"run-{stamp:%Y-%m-%d-%H%M}.jsonl"
n_model = n_fb = 0
with out.open("w") as f:
    f.write(json.dumps({"started": stamp.isoformat(timespec="seconds"), "model": os.path.basename(model or ""),
                        "machine": f"{platform.system()} {platform.machine()}, {os.cpu_count()} CPUs, no GPU"}) + "\n")
    for p in sorted((root / "examples").glob("*.txt")):
        text = p.read_text(); hits = scan(text); v = verdict(hits)
        a = advise(text, v, hits, model)
        n_model += a.meta.get("explanation_source") == "model"; n_fb += a.meta.get("reply_source") == "model"
        rec = {"example": p.stem, "verdict": v, "rules": [h.rule.id for h in hits], "source": a.source,
               "explanation": a.explanation, "reply": a.reply, **a.meta}
        f.write(json.dumps(rec) + "\n")
        print(f"{p.stem:28} {v:11} expl={a.meta.get('explanation_source','-'):8} reply={a.meta.get('reply_source','-'):8} {a.meta.get('gen_s','')}s {a.meta.get('reason','')}", flush=True)
print(f"model explanations kept: {n_model}/20, model replies kept: {n_fb}/20 -> {out.relative_to(root)}")
