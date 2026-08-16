"""Stage 1 regression gate: new engine (mood.json) vs old /parfbar quiz.

The old app.js sends the same answer keys PLUS intensity (unused by scoring).
Criterion (agreed): top-5 as a set matches AND the #1 position matches.
Run: python3 test_regression.py   (needs node for the engine part)
"""
import json
import subprocess
from pathlib import Path

from matcher_db import recommend_from_db

ENGINE_DIR = Path(__file__).parent.parent / "frontend" / "quiz-engine"

# 1. Run the JS engine simulation, capture the answers it produces
out = subprocess.run(["node", "test_engine.js"], cwd=ENGINE_DIR,
                     capture_output=True, text=True, check=True)
line = next(l for l in out.stdout.splitlines() if l.startswith("ANSWERS_JSON:"))
engine_answers = json.loads(line[len("ANSWERS_JSON:"):])

# 2. What the OLD parfbar quiz would send for the same clicks (incl. intensity)
old_answers = [
    {"branch": "dark_sexy", "sub_type": ["leather"], "vibe": ["night_out"],
     "notes": ["oud", "tobacco"], "intensity": ["rich"], "occasion": ["date"]},
    {"branch": "fresh_clean", "sub_type": ["citrus", "marine"], "vibe": ["luxury_hotel"],
     "notes": ["citrus", "musk"], "intensity": ["medium"], "occasion": ["office", "daily"],
     "budget": ["budget_1", "budget_2"]},
]

for i, (new_a, old_a) in enumerate(zip(engine_answers, old_answers), 1):
    new_top = recommend_from_db(new_a, store="parfbar", top_n=5)
    old_top = recommend_from_db(old_a, store="parfbar", top_n=5)
    new_set = {(r["brand"], r["name"]) for r in new_top}
    old_set = {(r["brand"], r["name"]) for r in old_top}
    assert new_set == old_set, (
        f"case {i}: top-5 sets differ\nnew: {sorted(new_set)}\nold: {sorted(old_set)}")
    assert (new_top[0]["brand"], new_top[0]["name"]) == (old_top[0]["brand"], old_top[0]["name"]), (
        f"case {i}: #1 differs: {new_top[0]['name']} vs {old_top[0]['name']}")
    print(f"case {i}: top-5 set + #1 match ✓  (#1 = {new_top[0]['brand']} — {new_top[0]['name']})")

print("test_regression: all OK — engine output scores identically to old /parfbar")
