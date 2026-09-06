"""Assert the chain still produces the numbers in expected.json.

This is the contract test. It runs against packages installed from PyPI, so a
failure means one project's release changed an output another project reads.
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent


def close(got: float, want: float, tol: float) -> bool:
    return abs(got - want) <= tol


def main(out_dir: str) -> int:
    out = pathlib.Path(out_dir)
    want = json.loads((HERE / "expected.json").read_text())
    tol = want["tolerance"]
    fit = json.loads((out / "fit.json").read_text())
    cal = json.loads((out / "calibration.json").read_text())
    panel = [json.loads(line) for line in (out / "panel_scored.jsonl").open()]
    majority = [json.loads(line) for line in (out / "majority_scored.jsonl").open()]

    checks: list[tuple[str, object, object]] = [
        ("panel.n_items", fit["n_items"], want["panel"]["n_items"]),
        ("panel.n_judges", len(fit["judges"]), want["panel"]["n_judges"]),
        ("panel.converged", fit["converged"], want["panel"]["converged"]),
        ("panel.prevalence_true", fit["class_prior"][1], want["panel"]["prevalence_true"]),
        (
            "panel.specificity_step_llama31_8b",
            fit["confusion"]["step:llama3.1:8b"][0][0],
            want["panel"]["specificity_step_llama31_8b"],
        ),
        (
            "panel.sensitivity_step_qwen25_14b",
            fit["confusion"]["step:qwen2.5:14b"][1][1],
            want["panel"]["sensitivity_step_qwen25_14b"],
        ),
        (
            "accuracy.panel",
            sum(r["y"] for r in panel) / len(panel),
            want["accuracy"]["panel"],
        ),
        (
            "accuracy.majority_vote",
            sum(r["y"] for r in majority) / len(majority),
            want["accuracy"]["majority_vote"],
        ),
        ("calibration.n", cal["n"], want["calibration"]["n"]),
        ("calibration.base_rate", cal["base_rate"], want["calibration"]["base_rate"]),
        ("calibration.brier", cal["brier"], want["calibration"]["brier"]),
        ("calibration.ece", cal["ece"], want["calibration"]["ece"]),
        (
            "calibration.spiegelhalter_z",
            cal["spiegelhalter_z"],
            want["calibration"]["spiegelhalter_z"],
        ),
        ("calibration.significant", cal["significant"], want["calibration"]["significant"]),
    ]

    failures = []
    for name, got, expected in checks:
        ok = (
            close(got, expected, tol)
            if isinstance(expected, float)
            else got == expected
        )
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {got!r}")
        if not ok:
            failures.append(f"{name}: got {got!r}, expected {expected!r}")

    if failures:
        print("\nthe chain no longer reproduces expected.json:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"\nall {len(checks)} checks passed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_chain.py <output-dir>")
    raise SystemExit(main(sys.argv[1]))
