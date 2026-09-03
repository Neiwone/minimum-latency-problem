#include "neighborhoods.h"
#include <algorithm>

using namespace std;

void neighborhood_swap(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN; i++) {
            for (int j = i + 1; j < sol.fN; j++) {
                if (sol.evaluateSwap(i, j)) {
                    swap(sol.fTour[i], sol.fTour[j]);
                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_reinsertion(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN; i++) {
            for (int j = 1; j < sol.fN; j++) {
                if (i == j) continue;

                if (sol.evaluateReinsertion(i, j)) {
                    int node = sol.fTour[i];

                    if (i < j) {
                        for (int k = i; k < j; k++)
                            sol.fTour[k] = sol.fTour[k + 1];

                        sol.fTour[j] = node;
                    }
                    else {
                        for (int k = i; k > j + 1; k--)
                            sol.fTour[k] = sol.fTour[k - 1];

                        sol.fTour[j + 1] = node;
                    }

                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_2opt(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN; i++) {
            for (int j = i + 1; j < sol.fN; j++) {
                if (sol.evaluate2Opt(i, j)) {
                    reverse(sol.fTour + i, sol.fTour + j + 1);
                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_oropt2(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN - 1; i++) {
            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= i + 1) continue;

                if (sol.evaluateOrOpt(i, i + 1, k)) {
                    int u = sol.fTour[i];
                    int v = sol.fTour[i + 1];

                    if (k > i + 1) {
                        for (int m = i; m <= k - 2; m++)
                            sol.fTour[m] = sol.fTour[m + 2];
                        sol.fTour[k - 1] = u;
                        sol.fTour[k]     = v;
                    } else {
                        for (int m = i + 1; m >= k + 3; m--)
                            sol.fTour[m] = sol.fTour[m - 2];
                        sol.fTour[k + 1] = u;
                        sol.fTour[k + 2] = v;
                    }

                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_oropt3(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN - 2; i++) {
            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= i + 2) continue;

                if (sol.evaluateOrOpt(i, i + 2, k)) {
                    int u = sol.fTour[i];
                    int v = sol.fTour[i + 1];
                    int w = sol.fTour[i + 2];

                    if (k > i + 2) {
                        for (int m = i; m <= k - 3; m++)
                            sol.fTour[m] = sol.fTour[m + 3];
                        sol.fTour[k - 2] = u;
                        sol.fTour[k - 1] = v;
                        sol.fTour[k]     = w;
                    } else {
                        for (int m = i + 2; m >= k + 4; m--)
                            sol.fTour[m] = sol.fTour[m - 3];
                        sol.fTour[k + 1] = u;
                        sol.fTour[k + 2] = v;
                        sol.fTour[k + 3] = w;
                    }

                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

/* ---------------------------------------------------------------------
 * H12a: Or-opt generalized to arbitrary segment length. Same shift-block
 * logic as neighborhood_oropt2/oropt3 above (verified to match them
 * exactly for segLen=2 and segLen=3), parameterized instead of
 * hand-duplicated per length. See docs/experiments/h12-extended-oropt.md.
 * ------------------------------------------------------------------- */

static void neighborhood_oropt_generic(Solution& sol, int segLen) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i + segLen - 1 < sol.fN; i++) {
            int j = i + segLen - 1;

            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= j) continue;

                if (sol.evaluateOrOpt(i, j, k)) {
                    vector<int> seg(sol.fTour + i, sol.fTour + j + 1);

                    if (k > j) {
                        for (int m = i; m <= k - segLen; m++)
                            sol.fTour[m] = sol.fTour[m + segLen];
                        for (int t = 0; t < segLen; t++)
                            sol.fTour[k - segLen + 1 + t] = seg[t];
                    } else {
                        for (int m = j; m >= k + 1 + segLen; m--)
                            sol.fTour[m] = sol.fTour[m - segLen];
                        for (int t = 0; t < segLen; t++)
                            sol.fTour[k + 1 + t] = seg[t];
                    }

                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

/* Public entry point for an arbitrary segment length -- used by the
   adaptive RVND (src/rvnd_adaptive.cpp), which decides at runtime which
   lengths to scan instead of having them hard-wired in the neighborhood
   list. Identical behavior to the fixed-length wrappers below. */
void neighborhood_oropt_len(Solution& sol, int segLen) {
    if (segLen < 2) return;
    neighborhood_oropt_generic(sol, segLen);
}

void neighborhood_oropt4(Solution& sol) { neighborhood_oropt_generic(sol, 4); }
void neighborhood_oropt5(Solution& sol) { neighborhood_oropt_generic(sol, 5); }
void neighborhood_oropt6(Solution& sol) { neighborhood_oropt_generic(sol, 6); }
void neighborhood_oropt8(Solution& sol) { neighborhood_oropt_generic(sol, 8); }
void neighborhood_oropt10(Solution& sol) { neighborhood_oropt_generic(sol, 10); }

/* H12b: genuine 3-opt -- reverse B=[i+1,j] and C=[j+1,k] independently,
   keeping their relative order. O(n^3) candidates, but each is O(1) via
   T/C/Cr, and empirically the full scan is fast (~30-170ms up to
   n=532 -- see docs/experiments/h12-extended-oropt.md section 12). */
void neighborhood_3opt_double_reversal(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN - 2; i++) {
            for (int j = i + 1; j < sol.fN - 1; j++) {
                for (int k = j + 1; k < sol.fN; k++) {
                    if (sol.evaluateThreeOptDoubleReversal(i, j, k)) {
                        reverse(sol.fTour + i + 1, sol.fTour + j + 1);
                        reverse(sol.fTour + j + 1, sol.fTour + k + 1);
                        sol.calculateStructures();
                        improved = true;
                    }
                }
            }
        }
    }
}

/* ---------------------------------------------------------------------
 * H4: multi-improvement variants. Scan the whole neighborhood against a
 * frozen T/C/Cr snapshot, keep every improving move whose position
 * footprint [lo,hi] doesn't overlap another already-chosen move's, apply
 * all chosen moves, then recompute once per batch instead of once per
 * move. Footprints are defined conservatively as the full range of
 * positions each move's apply-logic writes to (see docs/experiments/
 * h4-multi-improvement.md for why disjoint footprints make this exactly
 * equivalent to sequential first-improvement, not an approximation).
 * ------------------------------------------------------------------- */

namespace {

struct FootprintMove {
    int lo, hi;
};

/* Greedy activity selection: sort by footprint end, accept if it starts
   after the last accepted footprint's end **plus a 1-position buffer**.
   Maximizes count of disjoint moves (not total gain) -- evaluate*() only
   exposes a bool today, and preserving that (not touching the
   single-improvement code path) was a deliberate constraint.

   The buffer is required, not just non-overlap: every evaluate*() here
   computes a boundary edge via fDist[last][firstNode] against the
   position immediately *outside* its footprint (e.g. evaluate2Opt(i,j)
   reads fTour[j+1] to price the edge leaving the reversed segment). If a
   second move's footprint starts exactly at that neighboring position, it
   rewrites the very node the first move's evaluation assumed unchanged,
   silently invalidating its delta -- confirmed empirically: without this
   buffer, applying two such "disjoint" moves together sometimes
   *increased* cost despite both individually improving. */
template <typename Move, typename GetFootprint>
vector<Move> select_disjoint(vector<Move>& moves, GetFootprint footprint) {
    sort(moves.begin(), moves.end(), [&](const Move& a, const Move& b) {
        return footprint(a).hi < footprint(b).hi;
    });
    vector<Move> chosen;
    int lastEnd = -2; // so a footprint starting at position 0 is still accepted first
    for (const auto& m : moves) {
        FootprintMove fp = footprint(m);
        if (fp.lo > lastEnd + 1) {
            chosen.push_back(m);
            lastEnd = fp.hi;
        }
    }
    return chosen;
}

} // namespace

void neighborhood_swap_multi(Solution& sol) {
    bool improved = true;
    while (improved) {
        improved = false;

        struct Move { int i, j; };
        vector<Move> candidates;
        for (int i = 1; i < sol.fN; i++)
            for (int j = i + 1; j < sol.fN; j++)
                if (sol.evaluateSwap(i, j))
                    candidates.push_back({i, j});

        if (candidates.empty()) continue;

        auto chosen = select_disjoint<Move>(candidates, [](const Move& m) {
            return FootprintMove{m.i, m.j};
        });
        if (chosen.empty()) continue;

        for (const auto& m : chosen)
            swap(sol.fTour[m.i], sol.fTour[m.j]);

        sol.calculateStructures();
        improved = true;
    }
}

void neighborhood_reinsertion_multi(Solution& sol) {
    bool improved = true;
    while (improved) {
        improved = false;

        struct Move { int i, j; };
        vector<Move> candidates;
        for (int i = 1; i < sol.fN; i++)
            for (int j = 1; j < sol.fN; j++) {
                if (i == j) continue;
                if (sol.evaluateReinsertion(i, j))
                    candidates.push_back({i, j});
            }

        if (candidates.empty()) continue;

        auto chosen = select_disjoint<Move>(candidates, [](const Move& m) {
            return FootprintMove{min(m.i, m.j), max(m.i, m.j)};
        });
        if (chosen.empty()) continue;

        for (const auto& m : chosen) {
            int i = m.i, j = m.j;
            int node = sol.fTour[i];

            if (i < j) {
                for (int k = i; k < j; k++)
                    sol.fTour[k] = sol.fTour[k + 1];
                sol.fTour[j] = node;
            } else {
                for (int k = i; k > j + 1; k--)
                    sol.fTour[k] = sol.fTour[k - 1];
                sol.fTour[j + 1] = node;
            }
        }

        sol.calculateStructures();
        improved = true;
    }
}

void neighborhood_2opt_multi(Solution& sol) {
    bool improved = true;
    while (improved) {
        improved = false;

        struct Move { int i, j; };
        vector<Move> candidates;
        for (int i = 1; i < sol.fN; i++)
            for (int j = i + 1; j < sol.fN; j++)
                if (sol.evaluate2Opt(i, j))
                    candidates.push_back({i, j});

        if (candidates.empty()) continue;

        auto chosen = select_disjoint<Move>(candidates, [](const Move& m) {
            return FootprintMove{m.i, m.j};
        });
        if (chosen.empty()) continue;

        for (const auto& m : chosen)
            reverse(sol.fTour + m.i, sol.fTour + m.j + 1);

        sol.calculateStructures();
        improved = true;
    }
}

void neighborhood_oropt2_multi(Solution& sol) {
    bool improved = true;
    while (improved) {
        improved = false;

        struct Move { int i, k; };
        vector<Move> candidates;
        for (int i = 1; i < sol.fN - 1; i++)
            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= i + 1) continue;
                if (sol.evaluateOrOpt(i, i + 1, k))
                    candidates.push_back({i, k});
            }

        if (candidates.empty()) continue;

        auto chosen = select_disjoint<Move>(candidates, [](const Move& m) {
            return FootprintMove{min(m.i, m.k), max(m.i + 1, m.k)};
        });
        if (chosen.empty()) continue;

        for (const auto& m : chosen) {
            int i = m.i, k = m.k;
            int u = sol.fTour[i];
            int v = sol.fTour[i + 1];

            if (k > i + 1) {
                for (int mm = i; mm <= k - 2; mm++)
                    sol.fTour[mm] = sol.fTour[mm + 2];
                sol.fTour[k - 1] = u;
                sol.fTour[k]     = v;
            } else {
                for (int mm = i + 1; mm >= k + 3; mm--)
                    sol.fTour[mm] = sol.fTour[mm - 2];
                sol.fTour[k + 1] = u;
                sol.fTour[k + 2] = v;
            }
        }

        sol.calculateStructures();
        improved = true;
    }
}

void neighborhood_oropt3_multi(Solution& sol) {
    bool improved = true;
    while (improved) {
        improved = false;

        struct Move { int i, k; };
        vector<Move> candidates;
        for (int i = 1; i < sol.fN - 2; i++)
            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= i + 2) continue;
                if (sol.evaluateOrOpt(i, i + 2, k))
                    candidates.push_back({i, k});
            }

        if (candidates.empty()) continue;

        auto chosen = select_disjoint<Move>(candidates, [](const Move& m) {
            return FootprintMove{min(m.i, m.k), max(m.i + 2, m.k)};
        });
        if (chosen.empty()) continue;

        for (const auto& m : chosen) {
            int i = m.i, k = m.k;
            int u = sol.fTour[i];
            int v = sol.fTour[i + 1];
            int w = sol.fTour[i + 2];

            if (k > i + 2) {
                for (int mm = i; mm <= k - 3; mm++)
                    sol.fTour[mm] = sol.fTour[mm + 3];
                sol.fTour[k - 2] = u;
                sol.fTour[k - 1] = v;
                sol.fTour[k]     = w;
            } else {
                for (int mm = i + 2; mm >= k + 4; mm--)
                    sol.fTour[mm] = sol.fTour[mm - 3];
                sol.fTour[k + 1] = u;
                sol.fTour[k + 2] = v;
                sol.fTour[k + 3] = w;
            }
        }

        sol.calculateStructures();
        improved = true;
    }
}
