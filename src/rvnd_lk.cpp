#include "rvnd_lk.h"
#include "rvnd.h"
#include <bits/stdc++.h>

using namespace std;

/* Mirrors Solution::evaluate2Opt's computation, returns the signed
   delta instead of a boolean. See diag_lk.cpp for the derivation of the
   chain mechanics this is used in. */
static int delta_2opt(const Solution& sol, int i, int j) {
    if (i > j) swap(i, j);
    int t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = sol.getT(u, v);
        int Cu = sol.getC(u, v);
        int Wu = sol.getW(u, v);
        int firstNode = sol.fTour[u];
        int lastNode  = sol.fTour[v];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = sol.fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    auto appendReversed = [&](int u, int v) {
        if (u > v) return;
        int Tu = sol.getT(u, v);
        int Cu = sol.getCr(u, v);
        int Wu = sol.getW(u, v);
        int firstNode = sol.fTour[v];
        int lastNode  = sol.fTour[u];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = sol.fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    append(0, i - 1);
    appendReversed(i, j);
    append(j + 1, sol.fN - 1);

    return c - sol.fEvaluationValue;
}

/* Runs one chain in place on `s` (caller passes a throwaway copy),
   returning the tour at the best point visited (which may be the
   starting tour itself, if no step ever improved on it). */
static pair<int, vector<int>> run_chain(Solution& s, Evaluator& eval, int startPos,
                                         int maxDepth, int candK) {
    int n = s.fN;
    int baseCost = s.fEvaluationValue;
    int bestCost = baseCost;
    vector<int> bestTour(s.fTour, s.fTour + n);

    int freeEnd = startPos;

    for (int depth = 1; depth <= maxDepth; depth++) {
        vector<int> pos(n);
        for (int k = 0; k < n; k++) pos[s.fTour[k]] = k;

        int c1 = s.fTour[freeEnd];
        int bestDeltaStep = INT_MAX;
        int bestI = -1, bestJ = -1, bestPosC2 = -1;

        int kmax = min(candK, eval.fNearNumMax);
        for (int k = 1; k <= kmax; k++) {
            int c2 = eval.fNearCity[c1][k];
            if (c2 == 0) continue;
            int posC2 = pos[c2];
            if (posC2 == freeEnd) continue;

            int i, j;
            if (posC2 > freeEnd) { i = freeEnd + 1; j = posC2; }
            else                 { i = posC2;       j = freeEnd - 1; }
            if (i >= j) continue;

            int d = delta_2opt(s, i, j);
            if (d < bestDeltaStep) {
                bestDeltaStep = d;
                bestI = i; bestJ = j; bestPosC2 = posC2;
            }
        }

        if (bestI < 0) break;

        reverse(s.fTour + bestI, s.fTour + bestJ + 1);
        s.calculateStructures();
        freeEnd = bestPosC2;

        if (s.fEvaluationValue < bestCost) {
            bestCost = s.fEvaluationValue;
            bestTour.assign(s.fTour, s.fTour + n);
        }
    }

    return {bestCost, bestTour};
}

void RVND_LKEscape(Solution& sol, Evaluator& eval, mt19937& gen) {
    const int numProbes = 10;
    const int maxDepth = 10;
    const int candK = 12;

    RVND_ExtendedOrOpt(sol, gen);

    bool escaped = true;
    while (escaped) {
        escaped = false;
        int n = sol.fN;
        if (n < 4) break;

        vector<int> positions(n - 1);
        for (int p = 1; p < n; p++) positions[p - 1] = p;
        shuffle(positions.begin(), positions.end(), gen);

        int tries = min(numProbes, (int)positions.size());
        for (int t = 0; t < tries; t++) {
            Solution copy = sol;
            auto [bestCost, bestTour] = run_chain(copy, eval, positions[t], maxDepth, candK);
            if (bestCost < sol.fEvaluationValue) {
                for (int k = 0; k < n; k++) sol.fTour[k] = bestTour[k];
                sol.calculateStructures();
                escaped = true;
                break;
            }
        }

        if (escaped) RVND_ExtendedOrOpt(sol, gen);
    }
}
