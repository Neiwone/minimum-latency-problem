"""
Paired comparison of solver runs, used by every report in the project.

Runs are paired by seed: run i of a solver against run i of the baseline on
the same instance. Throughout, rel% = (solver - baseline) / baseline * 100 and
a win is a pair where the solver's cost is lower, so a negative rel% and
more wins than losses both mean the solver is better.
"""
import math
import statistics
from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple


def sign_test_p(wins: int, losses: int) -> float:
    """Two-sided exact sign test p-value; ties are left out."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p_le_k = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * p_le_k)


class Paired(NamedTuple):
    n: int
    mean_rel: float
    wins: int
    ties: int
    losses: int
    p: float


def compare_pairs(pairs: Iterable[Tuple[float, float]]) -> Optional[Paired]:
    """(baseline cost, solver cost) pairs -> their summary, or None if there
    are none."""
    rel, wins, ties, losses = [], 0, 0, 0
    for base, solver in pairs:
        rel.append((solver - base) / base * 100.0)
        if solver < base:
            wins += 1
        elif solver > base:
            losses += 1
        else:
            ties += 1
    if not rel:
        return None
    return Paired(len(rel), statistics.mean(rel), wins, ties, losses,
                  sign_test_p(wins, losses))


def split_key(key: str) -> Tuple[str, str, int]:
    """Checkpoint key "<instance>|<solver>|<seed>" -> its three parts."""
    inst, solver, seed = key.split("|")
    return inst, solver, int(seed)


def pair_runs(runs: Dict[str, Dict], baseline: str, solver: str,
              instances: Optional[Sequence[str]] = None,
              seeds: Optional[Iterable[int]] = None
              ) -> Dict[str, List[Tuple[Dict, Dict]]]:
    """
    For each instance, the (baseline record, solver record) of every seed
    both of them ran, in seed order. `instances` and `seeds` restrict the
    pairs to those (and `instances` sets the order); by default instances
    come in the order they first appear in `runs`. Instances without a
    single pair are left out.
    """
    if instances is None:
        instances = list(dict.fromkeys(split_key(k)[0] for k in runs))
    if seeds is None:
        seeds = sorted({split_key(k)[2] for k in runs})
    else:
        seeds = list(seeds)
    out = {}
    for inst in instances:
        pairs = [(runs[f"{inst}|{baseline}|{s}"], runs[f"{inst}|{solver}|{s}"])
                 for s in seeds
                 if f"{inst}|{baseline}|{s}" in runs and f"{inst}|{solver}|{s}" in runs]
        if pairs:
            out[inst] = pairs
    return out
