"""Response latency from stereo call recordings (left = caller, right = agent).

For every caller turn, latency = start of the agent's next speech - end of the caller's speech.
Usage: python measure_latency.py recordings/ > latency.csv
Recordings: recordings/<platform>/<lang>/<scenario>_<run>.wav
"""
import csv, sys, wave
from pathlib import Path

import numpy as np

FRAME_MS = 20
SPEECH_DB = -40.0       # frame is speech if RMS above this (dBFS)
MIN_SILENCE_MS = 700    # end of a turn = this much silence
MIN_SPEECH_MS = 200     # ignore blips shorter than this


def frames_db(x, sr):
    n = int(sr * FRAME_MS / 1000)
    x = x[: len(x) // n * n].reshape(-1, n).astype(np.float64)
    rms = np.sqrt((x ** 2).mean(axis=1)) + 1e-9
    return 20 * np.log10(rms / 32768.0)


def segments(active):
    """Speech segments as (start_frame, end_frame), merging short gaps and dropping blips."""
    segs, start, gap = [], None, 0
    max_gap = MIN_SILENCE_MS // FRAME_MS
    for i, a in enumerate(active):
        if a:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap >= max_gap:
                segs.append((start, i - gap + 1)); start, gap = None, 0
    if start is not None:
        segs.append((start, len(active)))
    return [s for s in segs if (s[1] - s[0]) * FRAME_MS >= MIN_SPEECH_MS]


def latencies(path):
    with wave.open(str(path)) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    if ch != 2:
        raise ValueError(f"{path}: expected stereo (caller left, agent right)")
    caller, agent = data[0::2], data[1::2]
    cs = segments(frames_db(caller, sr) > SPEECH_DB)
    ags = segments(frames_db(agent, sr) > SPEECH_DB)
    out = []
    for _, c_end in cs:
        nxt = next((a0 for a0, _ in ags if a0 >= c_end), None)
        if nxt is not None:
            out.append((nxt - c_end) * FRAME_MS)
    return out


def main(root):
    wr = csv.writer(sys.stdout)
    wr.writerow(["platform", "lang", "scenario", "run", "turn", "latency_ms"])
    for f in sorted(Path(root).glob("*/*/*.wav")):
        platform, lang = f.parts[-3], f.parts[-2]
        scenario, _, run = f.stem.rpartition("_")
        for i, ms in enumerate(latencies(f), 1):
            wr.writerow([platform, lang, scenario, run, i, ms])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "recordings")
