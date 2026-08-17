"""Analisa scripts/night_batch_results.json: rvnd-mode single vs extended-oropt (H12a)."""
import json
import math
import statistics
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def sign_test_p(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p_le_k = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2 * p_le_k)


def summarize(rows):
    diffs = [r["cost_single"] - r["cost_extended"] for r in rows]
    rel = [d / r["cost_single"] * 100 for d, r in zip(diffs, rows)]
    wins = sum(1 for d in diffs if d > 0)
    losses = sum(1 for d in diffs if d < 0)
    ties = len(rows) - wins - losses
    p = sign_test_p(wins, losses)
    ts = statistics.mean(r["time_single_ms"] for r in rows)
    te = statistics.mean(r["time_extended_ms"] for r in rows)
    time_pct = (te - ts) / ts * 100
    return statistics.mean(rel), wins, ties, losses, p, time_pct


def main():
    path = PROJECT_ROOT / "scripts" / "night_batch_results.json"
    results = json.load(open(path))

    by_instance = {}
    for r in results:
        by_instance.setdefault(r["instance"], []).append(r)

    print(f"{'instance':10} {'n':>4} {'mean_rel%':>10} {'w/t/l':>10} {'sign_p':>8} {'time+%':>8}")
    all_rows = []
    for instance, rows in by_instance.items():
        mean_rel, w, t, l, p, time_pct = summarize(rows)
        print(f"{instance:10} {len(rows):4d} {mean_rel:10.4f} {w}/{t}/{l:<6} {p:8.3f} {time_pct:8.1f}")
        all_rows.extend(rows)

    if all_rows:
        mean_rel, w, t, l, p, time_pct = summarize(all_rows)
        print(f"{'AGREGADO':10} {len(all_rows):4d} {mean_rel:10.4f} {w}/{t}/{l:<6} {p:8.3f} {time_pct:8.1f}")


if __name__ == "__main__":
    main()
