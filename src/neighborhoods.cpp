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

/* H12a: or-opt for any segment length -- the same shift-block logic as
   oropt2/oropt3, parameterized instead of duplicated per length. */

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

/* Runtime-chosen length, for the adaptive RVND. Same behaviour as the
   fixed-length wrappers below. */
void neighborhood_oropt_len(Solution& sol, int segLen) {
    if (segLen < 2) return;
    neighborhood_oropt_generic(sol, segLen);
}

void neighborhood_oropt4(Solution& sol) { neighborhood_oropt_generic(sol, 4); }
void neighborhood_oropt5(Solution& sol) { neighborhood_oropt_generic(sol, 5); }
void neighborhood_oropt6(Solution& sol) { neighborhood_oropt_generic(sol, 6); }
void neighborhood_oropt8(Solution& sol) { neighborhood_oropt_generic(sol, 8); }
void neighborhood_oropt10(Solution& sol) { neighborhood_oropt_generic(sol, 10); }

/* H12b: reverse B=[i+1,j] and C=[j+1,k] independently, keeping their
   order. O(n^3) candidates, each O(1); ~30-170ms up to n=532. */
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

/* H4: scan against a frozen snapshot, keep improving moves with disjoint
   position footprints, apply them all, recompute once per batch. */

namespace {

struct FootprintMove {
    int lo, hi;
};

/* Greedy activity selection by footprint end. The 1-position BUFFER is
   required: evaluate*() prices a boundary edge just outside its footprint. */
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

/* H16: relocate [i..i+segLen-1] REVERSED after position k. Applies by
   extract/reverse/reinsert -- in-place shifting does not survive a flip. */
void neighborhood_oropt_rev_len(Solution& sol, int segLen) {
    if (segLen < 2 || segLen >= sol.fN - 1) return;

    bool improved = true;
    vector<int> seg(segLen), rest;
    rest.reserve(sol.fN);

    while (improved) {
        improved = false;

        for (int i = 1; i + segLen - 1 < sol.fN; i++) {
            int j = i + segLen - 1;

            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= j) continue;

                if (!sol.evaluateOrOptReversed(i, j, k)) continue;

                int anchor = sol.fTour[k];

                for (int m = 0; m < segLen; m++)
                    seg[m] = sol.fTour[j - m];          /* reversed */

                rest.clear();
                for (int m = 0; m < sol.fN; m++)
                    if (m < i || m > j) rest.push_back(sol.fTour[m]);

                int pos = 0;
                for (int m = 0; m < (int)rest.size(); m++) {
                    sol.fTour[pos++] = rest[m];
                    if (rest[m] == anchor)
                        for (int q = 0; q < segLen; q++) sol.fTour[pos++] = seg[q];
                }

                sol.calculateStructures();
                improved = true;
                break;
            }
            if (improved) break;
        }
    }
}

void neighborhood_oropt_rev2(Solution& sol) { neighborhood_oropt_rev_len(sol, 2); }
void neighborhood_oropt_rev3(Solution& sol) { neighborhood_oropt_rev_len(sol, 3); }
void neighborhood_oropt_rev4(Solution& sol) { neighborhood_oropt_rev_len(sol, 4); }
void neighborhood_oropt_rev5(Solution& sol) { neighborhood_oropt_rev_len(sol, 5); }
void neighborhood_oropt_rev6(Solution& sol) { neighborhood_oropt_rev_len(sol, 6); }
