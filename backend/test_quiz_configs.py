"""Validate quiz configs: every maps value must hit a real scoring key
(typos here fail silently — zero points, no error), and different personas
must not all get the same top-5.
Run: python3 test_quiz_configs.py
"""
import json
from pathlib import Path

import matcher_db as m

QUIZ_DIR = Path(__file__).parent.parent / "frontend" / "quiz-engine" / "quizzes"

VALID = {
    "branch":   set(m.BRANCH_ACCORDS),
    "vibe":     set(m.VIBE_ACCORDS) | set(m.BRANCH_VIBE_ACCORDS),
    "sub_type": set(m.SUB_TYPE_ACCORDS),
    "notes":    set(m.NOTE_KEYWORDS),
    "occasion": set(m.OCCASION_ACCORDS),
    "season":   set(m.SEASON_ACCORDS),
    "budget":   {"budget_1", "budget_2", "budget_3", "budget_4"},
    "gender":   {"self", "unisex", "gift_male", "gift_female", "men", "women", ""},
}


def check_maps(maps: dict, where: str):
    for key, val in maps.items():
        assert key in VALID, f"{where}: maps key '{key}' is not a scoring field"
        vals = val if isinstance(val, list) else [val]
        for v in vals:
            assert v in VALID[key], f"{where}: maps.{key} value '{v}' unknown to scoring"


def iter_steps(config):
    shared = config.get("shared", {})
    for step in config.get("steps", []):
        yield shared[step["$ref"]] if "$ref" in step else step
    for br, steps in config.get("branches", {}).items():
        for step in steps:
            yield shared[step["$ref"]] if "$ref" in step else step


for path in sorted(QUIZ_DIR.glob("*.json")):
    config = json.loads(path.read_text())
    for step in iter_steps(config):
        assert step.get("options"), f"{path.name}: step {step.get('id')} has no options"
        for opt in step["options"]:
            where = f"{path.name}:{step['id']}:{opt['value']}"
            # config text must be pure ASCII-compatible where it matters (bg colors!)
            bg = opt.get("bg", "")
            assert all(ord(c) < 128 for c in bg), f"{where}: non-ASCII char in bg '{bg}'"
            if "maps" in opt:
                check_maps(opt["maps"], where)
            # answers-bound steps: value itself must be a valid scoring value
            sid = step["id"]
            if not sid.startswith("_") and sid in VALID:
                assert opt["value"] in VALID[sid], f"{where}: value not valid for '{sid}'"
    print(f"{path.name}: maps OK")

# Diversity: contrasting personas per quiz must not share an identical top-5
PERSONAS = {
    "characters.json": [
        {"branch": "dark_sexy", "vibe": ["dark_elegance", "night_out"], "notes": ["oud", "tobacco"],
         "occasion": ["night_city", "party"]},
        {"branch": "soft_skin", "sub_type": ["clean_musk"], "vibe": ["second_skin"],
         "notes": ["musk", "rose"], "occasion": ["daily"]},
        {"branch": "fresh_clean", "vibe": ["summer_europe"], "notes": ["citrus", "marine"],
         "occasion": ["travel"]},
    ],
    "places.json": [
        {"branch": "warm_cozy", "vibe": ["nordic_cabin"], "notes": ["woody", "vanilla"], "season": ["winter"]},
        {"branch": "elegant_luxury", "sub_type": ["hotel"], "vibe": ["luxury_hotel"], "notes": ["rose"], "season": ["spring"]},
        {"branch": "dark_sexy", "vibe": ["night_out"], "notes": ["oud"], "occasion": ["party"]},
    ],
    "moodboard.json": [
        {"branch": "dark_sexy", "vibe": ["dark_elegance", "night_out"], "notes": ["amber"]},
        {"branch": "fresh_clean", "vibe": ["beach", "summer_europe"], "notes": ["marine", "citrus"]},
        {"branch": "soft_skin", "vibe": ["just_showered"], "sub_type": ["powdery"], "notes": ["musk", "rose"]},
    ],
}

for quiz, personas in PERSONAS.items():
    tops = []
    for p in personas:
        recs = m.recommend_from_db(p, store="scentrique", top_n=5)
        tops.append(tuple((r["brand"], r["name"]) for r in recs))
    assert len(set(tops)) > 1, f"{quiz}: all personas got the same top-5 — flat mapping"
    overlap = set(tops[0]) & set(tops[1]) & set(tops[2])
    print(f"{quiz}: {len(set(tops))}/3 distinct top-5s, 3-way overlap {len(overlap)}/5")

print("test_quiz_configs: all OK")
