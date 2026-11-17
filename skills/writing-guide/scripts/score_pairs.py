#!/usr/bin/env python3
"""Score completed, order-swapped writing comparisons without making model calls."""

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys


GROUP_FIELDS = (
    "candidate_version", "baseline_version", "writer_model", "judge_model", "split"
)


def read_records(source):
    seen = set()
    records = []
    for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError("expected a JSON object")
            for field in ("case_id", *GROUP_FIELDS):
                if not isinstance(record.get(field), str) or not record[field].strip():
                    raise ValueError(f"{field} must be a nonempty string")
            if record["split"] not in ("dev", "test"):
                raise ValueError("split must be dev or test")
            if record["candidate_version"] == record["baseline_version"]:
                raise ValueError("candidate and baseline versions must differ")
            for direction in ("forward", "reverse"):
                judgment = record.get(direction)
                if not isinstance(judgment, dict):
                    raise ValueError(f"{direction} must contain a completed judgment")
                if judgment.get("winner") not in ("A", "B", "tie"):
                    raise ValueError(f"{direction}.winner must be A, B, or tie")
                for field in ("faithful_a", "faithful_b"):
                    if type(judgment.get(field)) is not bool:
                        raise ValueError(f"{direction}.{field} must be a boolean")
            identity = tuple(record[field] for field in (*GROUP_FIELDS, "case_id"))
            if identity in seen:
                raise ValueError("duplicate case in the same comparison")
            seen.add(identity)
            records.append(record)
        except (ValueError, TypeError) as error:
            raise ValueError(f"line {number}: {error}") from error
    if not records:
        raise ValueError("no completed comparison records")
    return records


def score(records):
    groups = defaultdict(Counter)
    for record in records:
        group = groups[tuple(record[field] for field in GROUP_FIELDS)]
        group["total_cases"] += 1
        forward, reverse = record["forward"], record["reverse"]
        candidate_faithful = forward["faithful_a"] and reverse["faithful_b"]
        baseline_faithful = forward["faithful_b"] and reverse["faithful_a"]
        group["candidate_faithfulness_failures"] += not candidate_faithful
        group["baseline_faithfulness_failures"] += not baseline_faithful
        if not candidate_faithful or not baseline_faithful:
            group["faithfulness_failed_cases"] += 1
            continue
        forward_winner = {"A": "candidate", "B": "baseline", "tie": "tie"}[forward["winner"]]
        reverse_winner = {"A": "baseline", "B": "candidate", "tie": "tie"}[reverse["winner"]]
        if forward_winner != reverse_winner:
            group["order_sensitive_cases"] += 1
        else:
            outcome = {
                "candidate": "candidate_wins", "baseline": "baseline_wins", "tie": "ties"
            }[forward_winner]
            group[outcome] += 1

    reports = []
    counters = (
        "total_cases", "candidate_wins", "baseline_wins", "ties", "order_sensitive_cases",
        "faithfulness_failed_cases", "candidate_faithfulness_failures", "baseline_faithfulness_failures",
    )
    for identity, counts in sorted(groups.items()):
        report = dict(zip(GROUP_FIELDS, identity))
        report.update({name: counts[name] for name in counters})
        decisive = counts["candidate_wins"] + counts["baseline_wins"]
        report["stable_decisive_cases"] = decisive
        report["candidate_win_rate_among_stable_decisions"] = (
            round(counts["candidate_wins"] / decisive, 6) if decisive else None
        )
        report["candidate_wins_divided_by_all_cases"] = round(
            counts["candidate_wins"] / counts["total_cases"], 6
        )
        reports.append(report)
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("judgments", type=Path, help="JSONL file with forward and reverse judgments")
    args = parser.parse_args()
    try:
        reports = score(read_records(args.judgments))
    except (OSError, ValueError) as error:
        parser.error(str(error))
    json.dump({"comparisons": reports}, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
