"""Check the browser engine (docs/engine.js) gives the same verdict and rules as Python on every example."""
import json, subprocess, sys
from pathlib import Path
from second_look.rules import scan, verdict

root = Path(__file__).resolve().parent.parent
js = """const {EXAMPLES}=require('./docs/data.js');const E=require('./docs/engine.js');
console.log(JSON.stringify(EXAMPLES.map(x=>{const h=E.scan(x.text);return [x.name,E.verdict(h),Object.fromEntries(h.map(y=>[y.rule.id,y.evidence]))]})));"""
out = json.loads(subprocess.run(["node", "-e", js], cwd=root, capture_output=True, text=True, check=True).stdout)
bad = 0
for name, v, ev in out:
    hits = scan((root / "examples" / f"{name}.txt").read_text().strip())
    py = (verdict(hits), {h.rule.id: h.evidence for h in hits})
    ok = py == (v, ev)  # same verdict, same rules, same matched words
    bad += not ok
    print(f"{'OK  ' if ok else 'DIFF'} {name:28} py={py[0]:11} js={v}")
print(f"{len(out) - bad}/{len(out)} match")
sys.exit(1 if bad else 0)
