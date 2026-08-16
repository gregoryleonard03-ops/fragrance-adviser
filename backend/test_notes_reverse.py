"""Guard against the silent-failure mode of _NOTES_REVERSE: if the LLM answers
in a language whose keys are missing, notes are dropped with no error.
Run: python3 test_notes_reverse.py
"""
from social_analyzer import _NOTES_REVERSE, social_to_answers, analyze_with_claude
import matcher_db

# 1. Every note key must map to a real NOTE_KEYWORDS bucket in the matcher
for note, bucket in _NOTES_REVERSE.items():
    assert bucket in matcher_db.NOTE_KEYWORDS, f"_NOTES_REVERSE['{note}'] → '{bucket}' is not a NOTE_KEYWORDS key"

# 2. Typical EN notes (incl. the exact examples the EN prompt shows the LLM) resolve
for note in ["bergamot", "white musk", "peony", "sandalwood", "oud", "vanilla",
             "jasmine", "amber", "leather", "vetiver", "sea salt", "pink pepper"]:
    assert note in _NOTES_REVERSE, f"EN note '{note}' missing from _NOTES_REVERSE — IG→notes link silently dead"

# 3. Same for the RU examples (biblioteka demo must keep working)
for note in ["бергамот", "белый мускус", "пион", "сандал", "уд", "ваниль"]:
    assert note in _NOTES_REVERSE, f"RU note '{note}' missing from _NOTES_REVERSE"

# 4. End-to-end: an EN analysis yields non-empty notes in answers
answers = social_to_answers({
    "dominant_vibe": "woody", "aesthetic": "clean_minimal",
    "lifestyles": ["professional"], "age_group": "adult",
    "notes_hint": ["bergamot", "cedarwood", "white musk"],
})
assert answers["notes"], f"EN notes_hint produced empty notes: {answers}"
assert set(answers["notes"]) == {"citrus", "woody", "musk"}, answers["notes"]

# 5. Both prompt languages actually ask for the right language
import inspect
src = inspect.getsource(analyze_with_claude)
assert '"bergamot", "white musk", "peony"' in src, "EN notes example missing from prompt"
assert '"бергамот", "белый мускус", "пион"' in src, "RU notes example missing from prompt"

print("test_notes_reverse: all OK")
