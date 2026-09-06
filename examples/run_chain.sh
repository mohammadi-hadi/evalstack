#!/usr/bin/env bash
# Chain A end to end: judgepanel -> join -> calikit -> abeval.
# Reads trajectory-judge's committed verdicts, pinned to a commit so the
# numbers cannot move under us. Writes into $OUT (default: a temp dir).
set -euo pipefail

SHA="ab5ac1283bf2804e213a177503deabd82deb705b"
RAW="https://raw.githubusercontent.com/mohammadi-hadi/trajectory-judge/${SHA}/results/raw"
HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT:-$(mktemp -d)}"

echo "==> fetching the panel (trajectory-judge @ ${SHA:0:7})"
curl -fsSL "$RAW/verdicts.jsonl"     -o "$OUT/verdicts.jsonl"
curl -fsSL "$RAW/trajectories.jsonl" -o "$OUT/trajectories.jsonl"

echo "==> 1. estimate every judge's accuracy, with no gold labels"
judgepanel fit "$OUT/verdicts.jsonl" \
  --item-key trajectory_id --judge-key judge_id --label-key faulty \
  --positive true --bootstrap 0 --json \
  --labels-out "$OUT/panel_labels.jsonl" > "$OUT/fit.json"

echo "==> 2. check the independence assumption before believing step 1"
judgepanel agree "$OUT/verdicts.jsonl" \
  --item-key trajectory_id --judge-key judge_id --label-key faulty \
  --json > "$OUT/agree.json"

echo "==> 3. join the panel's labels to gold"
python3 "$HERE/join_gold.py"     "$OUT/panel_labels.jsonl" "$OUT/trajectories.jsonl" > "$OUT/panel_scored.jsonl"
python3 "$HERE/majority_vote.py" "$OUT/verdicts.jsonl"     "$OUT/trajectories.jsonl" > "$OUT/majority_scored.jsonl"

echo "==> 4. are the panel's confidences honest?"
calikit audit "$OUT/panel_scored.jsonl" --json > "$OUT/calibration.json"

echo "==> 5. does the panel actually beat majority vote?"
abeval compare "$OUT/majority_scored.jsonl" "$OUT/panel_scored.jsonl" \
  --id-key item --metric y | tee "$OUT/compare.txt"

echo "==> outputs in $OUT"
