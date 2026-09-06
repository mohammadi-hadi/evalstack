"""Score plain majority vote on the same panel, as the baseline judgepanel has to beat.

Reads trajectory-judge's verdicts and gold, writes {"item", "y"} per item --
abeval's input format, so `abeval compare` can put the two side by side.

    python majority_vote.py verdicts.jsonl trajectories.jsonl > majority_scored.jsonl
"""

import collections
import json
import sys


def main(verdicts_path: str, gold_path: str) -> None:
    gold = {}
    with open(gold_path) as handle:
        for line in handle:
            row = json.loads(line)
            gold[row["trajectory_id"]] = bool(row["label"]["faulty"])

    votes = collections.defaultdict(list)
    with open(verdicts_path) as handle:
        for line in handle:
            row = json.loads(line)
            votes[row["trajectory_id"]].append(bool(row["faulty"]))

    for item, cast in sorted(votes.items()):
        predicted = sum(cast) * 2 > len(cast)
        print(json.dumps({"item": item, "y": int(predicted == gold[item])}))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
