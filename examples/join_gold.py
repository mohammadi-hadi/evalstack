"""Join judgepanel's aggregated labels to gold, so calikit and abeval can read them.

judgepanel writes {"item", "label", "p"} per item, where `p` is the posterior
probability of the label it chose. Gold lives in trajectory-judge's
trajectories.jsonl as label.faulty. This adds `y`: 1 when the panel was right.

The result is one file that both downstream tools read unchanged --
calikit wants (p, y), abeval wants (--id-key item --metric y).

    python join_gold.py panel_labels.jsonl trajectories.jsonl > panel_scored.jsonl
"""

import json
import sys


def main(labels_path: str, gold_path: str) -> None:
    gold = {}
    with open(gold_path) as handle:
        for line in handle:
            row = json.loads(line)
            gold[row["trajectory_id"]] = bool(row["label"]["faulty"])

    with open(labels_path) as handle:
        for line in handle:
            row = json.loads(line)
            item = row["item"]
            if item not in gold:
                raise SystemExit(f"no gold label for item {item!r}")
            predicted = row["label"] == "true"
            row["y"] = int(predicted == gold[item])
            print(json.dumps(row))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
