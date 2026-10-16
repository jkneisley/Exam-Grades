#!/usr/bin/env python3
"""Suggest outcome-level grades from question-level exam scores.

Input scores CSV columns: student, outcome, question, level (D/C/B), score
  score is 10, 7.5, 5, 1, 0 or the letters S, G, L, N, X.
Outcomes CSV columns: outcome, points   (gradebook points for the outcome)
Optional overrides CSV columns: student, outcome, category (S/G/L/N/X)

Writes two files: a detailed report (with review flags) and an LMS-ready
wide file with one row per student and one column per outcome (points).
"""
import argparse
import csv
from collections import defaultdict

SCORE_TO_CAT = {10: "S", 7.5: "G", 5: "L", 1: "N", 0: "X"}
LETTER = {"S": 10.0, "G": 7.5, "L": 5.0, "N": 1.0, "X": 0.0}
CAT_PERCENT = {"S": 1.0, "G": 0.75, "L": 0.5, "N": 0.1, "X": 0.0}
# Harder-level questions count less toward readiness; D-level is foundational.
LEVEL_WEIGHT = {"D": 3.0, "C": 2.0, "B": 1.0}
# (minimum weighted average on the 0-10 scale, category), checked in order.
THRESHOLDS = [(9.0, "S"), (6.5, "G"), (3.0, "L"), (0.5, "N")]
CAT_ORDER = ["X", "N", "L", "G", "S"]


def parse_score(raw):
    raw = str(raw).strip().upper()
    if raw in LETTER:
        return LETTER[raw]
    value = float(raw)
    if value not in SCORE_TO_CAT:
        raise ValueError("invalid question score: %r" % raw)
    return value


def category_for_average(avg):
    for minimum, cat in THRESHOLDS:
        if avg >= minimum:
            return cat
    return "X"


def suggest(questions):
    """questions: list of (level, score). Returns (category, review, reason)."""
    scores = [s for _, s in questions]
    if all(s == scores[0] for s in scores):
        return SCORE_TO_CAT[scores[0]], False, "uniform scores"
    weights = [LEVEL_WEIGHT[lvl] for lvl, _ in questions]
    avg = sum(w * s for w, (_, s) in zip(weights, questions)) / sum(weights)
    cat = category_for_average(avg)
    reasons = ["weighted average %.2f" % avg]
    # A D-level miss means the student is not ready for the next course.
    d_scores = [s for lvl, s in questions if lvl == "D"]
    if d_scores and min(d_scores) <= 5 and CAT_ORDER.index(cat) > CAT_ORDER.index("G"):
        cat = "G"
        reasons.append("capped at G: D-level question scored L or lower")
    review = max(scores) - min(scores) >= 5
    if review:
        reasons.append("wide spread of question scores")
    if len({lvl for lvl, _ in questions}) > 1:
        review = True
        reasons.append("mixed mastery levels")
    if cat == "L":
        review = True
        reasons.append("L is ambiguous: check amount of correct work")
    return cat, review, "; ".join(reasons)


def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def grade(scores_rows, points, overrides=None):
    overrides = overrides or {}
    groups = defaultdict(list)
    for r in scores_rows:
        level = r["level"].strip().upper()
        if level not in LEVEL_WEIGHT:
            raise ValueError("invalid level %r" % level)
        key = (r["student"].strip(), r["outcome"].strip())
        groups[key].append((level, parse_score(r["score"])))
    results = []
    for (student, outcome), qs in sorted(groups.items()):
        cat, review, reason = suggest(qs)
        if (student, outcome) in overrides:
            cat, review, reason = overrides[(student, outcome)], False, "instructor override"
        possible = float(points[outcome])
        results.append({
            "student": student, "outcome": outcome, "category": cat,
            "percent": CAT_PERCENT[cat] * 100,
            "points": round(CAT_PERCENT[cat] * possible, 2),
            "possible": possible, "review": "YES" if review else "",
            "reason": reason,
        })
    return results


def write_outputs(results, report_path, lms_path):
    fields = ["student", "outcome", "category", "percent", "points",
              "possible", "review", "reason"]
    with open(report_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results)
    outcomes = sorted({r["outcome"] for r in results})
    students = sorted({r["student"] for r in results})
    by = {(r["student"], r["outcome"]): r["points"] for r in results}
    with open(lms_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["student"] + outcomes)
        for s in students:
            w.writerow([s] + [by.get((s, o), "") for o in outcomes])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("scores")
    p.add_argument("outcomes")
    p.add_argument("--overrides")
    p.add_argument("--report", default="report.csv")
    p.add_argument("--lms", default="lms.csv")
    a = p.parse_args(argv)
    points = {r["outcome"].strip(): r["points"] for r in read_csv(a.outcomes)}
    overrides = {}
    if a.overrides:
        for r in read_csv(a.overrides):
            overrides[(r["student"].strip(), r["outcome"].strip())] = r["category"].strip().upper()
    results = grade(read_csv(a.scores), points, overrides)
    write_outputs(results, a.report, a.lms)
    flagged = sum(1 for r in results if r["review"])
    print("%d outcome grades written; %d flagged for review" % (len(results), flagged))


if __name__ == "__main__":
    main()
