"""merge_answers: quiz + Instagram → one answers dict. Assert-based, no frameworks.
Run: python3 test_merge.py
"""
from social_analyzer import merge_answers, IG_MAX_VIBES

quiz = {"branch": "dark_sexy", "vibe": ["night_out"], "notes": ["oud"],
        "occasion": ["date"], "budget": ["budget_2"], "gender": ""}

# 1. Empty IG → quiz passes through untouched
m = merge_answers(quiz, {})
assert m["branch"] == "dark_sexy" and m["vibe"] == ["night_out"] and m["budget"] == ["budget_2"], m
m2 = merge_answers(quiz, None)
assert m2["vibe"] == ["night_out"], m2

# 2. Branch conflict → quiz wins; empty quiz string → IG fills in
ig = {"vibe": ["second_skin", "just_showered"], "notes": ["musk"], "gender": "women",
      "occasion": ["office"], "budget": [], "season": []}
m = merge_answers(quiz, ig)
assert m["branch"] == "dark_sexy", m
assert m["gender"] == "women", m  # quiz had "", IG fills

# 3. Overlapping vibe lists → union, quiz first, no dupes
m = merge_answers({"vibe": ["night_out", "second_skin"]}, {"vibe": ["second_skin", "dominant"]})
assert m["vibe"] == ["night_out", "second_skin", "dominant"], m

# 4. IG vibes clamped to IG_MAX_VIBES so IG can't shout the quiz down
loud_ig = {"vibe": ["a", "b", "c", "d"]}
m = merge_answers({"vibe": ["q"]}, loud_ig)
assert m["vibe"] == ["q"] + loud_ig["vibe"][:IG_MAX_VIBES], m

# 5. IG-only keys survive; quiz-only keys survive
m = merge_answers({"notes": ["oud"]}, {"occasion": ["travel"]})
assert m["notes"] == ["oud"] and m["occasion"] == ["travel"], m

# 6. Inputs not mutated
q_in = {"vibe": ["q"]}; ig_in = {"vibe": ["a", "b", "c"]}
merge_answers(q_in, ig_in)
assert q_in == {"vibe": ["q"]} and ig_in == {"vibe": ["a", "b", "c"]}, (q_in, ig_in)

print("test_merge: all OK")
