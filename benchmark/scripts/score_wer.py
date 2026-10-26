"""Word error rate of each platform's transcript on the scenario test phrases.

Usage: python score_wer.py transcripts/ > wer.csv
Transcripts: transcripts/<platform>/<lang>/<scenario>_<run>.txt (the agent-side transcript of the caller's words)
"""
import csv, json, re, sys, unicodedata
from pathlib import Path

import jiwer

SCEN = Path(__file__).resolve().parent.parent / "scenarios"


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))  # accents don't count as errors
    return re.sub(r"[^\w\s]", " ", s).split()


def best_window_wer(phrase, text):
    """WER of the phrase against the best-matching window of the transcript."""
    p, t = norm(phrase), norm(text)
    if not t:
        return 1.0
    n = len(p)
    best = 1.0
    for i in range(max(1, len(t) - n + 1)):
        for k in (n - 1, n, n + 1):
            win = t[i : i + max(1, k)]
            best = min(best, jiwer.wer(" ".join(p), " ".join(win)))
    return best


def main(root):
    wr = csv.writer(sys.stdout)
    wr.writerow(["platform", "lang", "scenario", "run", "phrase", "wer"])
    for f in sorted(Path(root).glob("*/*/*.txt")):
        platform, lang = f.parts[-3], f.parts[-2]
        scenario, _, run = f.stem.rpartition("_")
        spec = json.loads((SCEN / f"{scenario}.json").read_text())
        for phrase in spec.get("test_phrases", {}).get(lang[:2], []):
            wr.writerow([platform, lang, scenario, run, phrase, round(best_window_wer(phrase, f.read_text()), 3)])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "transcripts")
