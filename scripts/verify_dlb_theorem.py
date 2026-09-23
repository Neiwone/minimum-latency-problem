#!/usr/bin/env python3
"""
Brute-force check of the claim the don't-look bits rest on.

CLAIM. Let W = [a,b] be a window of tour positions, and let sigma be any
reordering of the cities inside W (everything outside untouched). Let mu be a
move whose support lies entirely OUTSIDE [a-1, b+1]. Then mu's gain --
cost(after mu) - cost(before mu) -- is the same before and after the
reordering.

So a city far from a perturbation cannot have changed its mind about whether a
move improves, which is exactly what lets the search skip it.

The script also checks the boundary: a move whose support touches a-1 or b+1
DOES change gain, so the one-position margin is necessary, not padding.

Nothing here reuses the solver's arithmetic: every cost is recomputed from
scratch by summing arrival times.
"""
import argparse
import random


def cost(tour, D):
    """Sum of arrival times -- the MLP objective, computed the slow honest way."""
    walked = total = 0
    for i in range(1, len(tour)):
        walked += D[tour[i - 1]][tour[i]]
        total += walked
    return total


def apply_perm(tour, lo, hi, perm):
    out = tour[:]
    out[lo:hi + 1] = [tour[p] for p in perm]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=200000)
    ap.add_argument("--n", type=int, default=14)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    n = args.n
    same = differ = boundary_differ = boundary_total = 0

    for _ in range(args.trials):
        D = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                D[i][j] = D[j][i] = rng.randint(1, 50)

        tour = [0] + rng.sample(range(1, n), n - 1)

        # the disturbed window
        a = rng.randint(2, n - 4)
        b = rng.randint(a, min(a + 3, n - 3))
        block = tour[a:b + 1]
        rng.shuffle(block)
        sigma = tour[:a] + block + tour[b + 1:]

        # a move supported strictly outside [a-1, b+1]
        if rng.random() < 0.5:
            lo = b + 2
            if lo >= n - 1:
                continue
            hi = rng.randint(lo, n - 1)
        else:
            hi = a - 2
            if hi < 2:
                continue
            lo = rng.randint(1, hi)

        perm = list(range(lo, hi + 1))
        rng.shuffle(perm)
        gain_before = cost(apply_perm(tour, lo, hi, perm), D) - cost(tour, D)
        gain_after = cost(apply_perm(sigma, lo, hi, perm), D) - cost(sigma, D)
        if gain_before == gain_after:
            same += 1
        else:
            differ += 1

        # the same test with the support touching the boundary b+1
        lo2 = b + 1
        if lo2 <= n - 2:
            hi2 = rng.randint(lo2 + 1, n - 1)
            perm2 = list(range(lo2, hi2 + 1))
            rng.shuffle(perm2)
            boundary_total += 1
            if (cost(apply_perm(tour, lo2, hi2, perm2), D) - cost(tour, D)) != \
               (cost(apply_perm(sigma, lo2, hi2, perm2), D) - cost(sigma, D)):
                boundary_differ += 1

    print(f"random tours of n={n}, {args.trials} trials, seed {args.seed}\n")
    print("THEOREM -- support strictly outside [a-1, b+1]:")
    print(f"  gain unchanged : {same}")
    print(f"  gain changed   : {differ}     (must be 0)")
    print("\nBOUNDARY -- support touching b+1, where the theorem stops applying:")
    print(f"  gain changed   : {boundary_differ} of {boundary_total}"
          f"     (must be > 0, or the margin would be pointless)")

    ok = differ == 0 and boundary_differ > 0
    print("\n" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
