"""Open the replay segments that the AEB change made differ (GUIDE.md, step 1).   python3 peek.py > evidence/peek_aeb.txt
Segment numbers come from the `open them: [...]` line of step 1 (evidence/replay.json, behaviour_change_aeb)."""
import json

import numpy as np

from lab12 import config as C, replay as R

segs = R.read_log(C.WORK_DIR / "replay_log.jsonl")
golden, _ = R.replay(segs, lambda: R.IDMStream())
aeb, _ = R.replay(segs, lambda: R.IDMStream(aeb_ttc=1.5))
opened = json.loads((C.EVID_DIR / "replay.json").read_text())["behaviour_change_aeb"]["differing_segments"]
print(f"segments that differ beyond tolerance: {opened}")
for seg in opened[:3]:
    frames = np.flatnonzero(np.abs(golden[seg] - aeb[seg]) > 1e-3)
    perc = [m for m in segs[seg] if m["topic"] == "/perception"]
    can = [m for m in segs[seg] if m["topic"] == "/can"]
    print(f"\nsegment {seg}: {len(frames)} of {len(perc)} frames differ: {frames.tolist()}")
    for k in frames[:5]:
        closing = can[k]["v_ego"] - perc[k]["v_lead"]
        print(f"  frame {k}: gap {perc[k]['gap']} closing {closing:.2f} TTC {perc[k]['gap'] / closing:.2f}  "
              f"old command {golden[seg, k]:.2f} -> new {aeb[seg, k]:.2f}")
    same = [(perc[k]["gap"] / cl, golden[seg, k]) for k in range(len(perc)) if k not in frames
            for cl in [can[k]["v_ego"] - perc[k]["v_lead"]] if cl > 1e-3]
    if same:
        t, cmd = min(same)
        print(f"  lowest TTC among the unchanged frames: {t:.2f} s (old command there {cmd:.2f}: already at or below -6)"
              if t < 1.5 else f"  lowest TTC among the unchanged frames: {t:.2f} s (above the 1.5 s AEB threshold)")
