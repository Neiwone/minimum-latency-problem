#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* Diagnostic for the Lin-Kernighan-style variable-depth idea.

   Classic LK's gain criterion ("new edge shorter than the one removed")
   is additive over edge lengths, which is only valid for edge-additive
   costs -- it is WRONG for MLP's cumulative latency, where an edge's
   contribution depends on how many customers come after it. This probe
   replaces that criterion with the EXACT total cost via the existing
   T/C/Cr concatenation tables (delta_2opt below, mirrors
   Solution::evaluate2Opt), so every step is evaluated honestly.

   Unlike H10 (dynasearch), which needed to search over combinations of
   SIMULTANEOUS disjoint reversals and hit a genuine Pareto-front
   complication (T and C don't decompose into a scalar DP), an LK chain
   is SEQUENTIAL: each step commits to one 2-opt-style reversal, applied
   for real (fTour mutated, T/C/Cr recomputed via calculateStructures),
   before considering the next. That avoids the DP entirely, at the cost
   of an O(n^2) recompute per step -- acceptable since depth and the
   number of chain attempts are both small.

   Question: starting from a solution already converged by
   RVND_ExtendedOrOpt (H12a's best known local search -- so no single
   swap/2-opt/reinsertion/or-opt(1..6) move improves it), can a chain of
   several sequential 2-opt-style moves, guided by nearest-neighbor
   candidate lists and allowed to pass through temporarily worse tours,
   ever reach a strictly better tour than the one RVND converged to?
   If never: RVND's neighborhoods already reach everything a bounded-depth
   sequential search reaches, and that itself is a useful, cheap null
   result. If sometimes: it's worth building this into a real
   neighborhood/algorithm.

   Chain mechanics (positions, not city ids; depot is fixed at position
   0 and is never part of a reversed range or a free end):

   Given the current tour and a "free end" position `freeEnd` holding
   city c1, and a nearest-neighbor candidate c2 (from Evaluator::
   fNearCity[c1]) currently at position posC2:
     - if posC2 > freeEnd: reverse [freeEnd+1, posC2]
     - if posC2 < freeEnd: reverse [posC2, freeEnd-1]
   Both cases make (c1, c2) a new tour edge (verified by hand against
   Solution::evaluate2Opt's own derivation: reversing [i,j] creates edges
   (tour[i-1], tour[j]) and (tour[i], tour[j+1])). In both cases the new
   free end is exactly posC2 -- the old neighbor of c1 ends up there,
   dangling toward whatever was on the other side of c2 -- so the chain
   continues from there without any extra bookkeeping. */

int delta_2opt(const Solution& sol, int i, int j) {
    if (i > j) swap(i, j);
    int n = sol.fN;

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
    append(j + 1, n - 1);

    (void)n;
    return c - sol.fEvaluationValue;
}

struct ChainResult {
    int bestDelta = 0;       // most negative cost improvement seen along the chain (<=0)
    int depthOfBest = 0;     // how many steps were taken to reach it
    int stepsTaken = 0;
};

/* Mutates `s` in place (caller must pass a throwaway copy). */
ChainResult run_chain(Solution& s, Evaluator& eval, int startPos, int maxDepth, int candK) {
    int n = s.fN;
    int baseCost = s.fEvaluationValue;
    int bestCost = baseCost;

    ChainResult res;
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
            if (c2 == 0) continue;              // never touch the depot
            int posC2 = pos[c2];
            if (posC2 == freeEnd) continue;

            int i, j;
            if (posC2 > freeEnd) { i = freeEnd + 1; j = posC2; }
            else                 { i = posC2;       j = freeEnd - 1; }
            if (i >= j) continue;   // i==j is a single-element no-op (c2 already adjacent to c1)

            int d = delta_2opt(s, i, j);
            if (d < bestDeltaStep) {
                bestDeltaStep = d;
                bestI = i; bestJ = j; bestPosC2 = posC2;
            }
        }

        if (bestI < 0) break;   // no viable candidate at all

        reverse(s.fTour + bestI, s.fTour + bestJ + 1);
        s.calculateStructures();
        freeEnd = bestPosC2;
        res.stepsTaken = depth;

        if (getenv("LK_VERBOSE"))
            cerr << "  depth=" << depth << " reverse[" << bestI << "," << bestJ
                 << "] stepDelta=" << bestDeltaStep
                 << " costNow=" << s.fEvaluationValue
                 << " relBase=" << (s.fEvaluationValue - baseCost) << "\n";

        if (s.fEvaluationValue < bestCost) {
            bestCost = s.fEvaluationValue;
            res.bestDelta = bestCost - baseCost;
            res.depthOfBest = depth;
        }
    }

    return res;
}

int full_route_cost(const Solution& s) {
    int t = 0, total = 0;
    for (int i = 1; i < s.fN; i++) {
        t += s.fDist[s.fTour[i - 1]][s.fTour[i]];
        total += t;
    }
    return total;
}

bool is_valid_permutation(const Solution& s) {
    vector<int> seen(s.fN, 0);
    for (int i = 0; i < s.fN; i++) {
        int c = s.fTour[i];
        if (c < 0 || c >= s.fN || seen[c]) return false;
        seen[c] = 1;
    }
    return s.fTour[0] == 0;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: ./diag_lk <instance.tsp> [--seed N] [--trials T] "
                "[--starts S] [--depth D] [--cand-k K]\n";
        return 1;
    }

    string instanceFile = argv[1];
    long seed = -1;
    int trials = 5;
    int starts = 30;
    int maxDepth = 6;
    int candK = 10;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
        else if (a == "--trials" && i + 1 < argc) trials = stoi(argv[++i]);
        else if (a == "--starts" && i + 1 < argc) starts = stoi(argv[++i]);
        else if (a == "--depth" && i + 1 < argc) maxDepth = stoi(argv[++i]);
        else if (a == "--cand-k" && i + 1 < argc) candK = stoi(argv[++i]);
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    long totalStarts = 0, totalEscapes = 0;
    int bestDeltaOverall = 0;

    for (int t = 0; t < trials; t++) {
        Solution s;
        construction(s, eval, 0.15, gen);
        RVND_ExtendedOrOpt(s, gen);

        int baseCost = s.fEvaluationValue;
        int n = s.fN;

        int trialBestDelta = 0;
        int escapesThisTrial = 0;

        int numStarts = min(starts, n - 1);
        vector<int> positions(n - 1);
        for (int p = 1; p < n; p++) positions[p - 1] = p;
        shuffle(positions.begin(), positions.end(), gen);

        for (int si = 0; si < numStarts; si++) {
            Solution copy = s;   // deep copy, fresh T/C/Cr
            ChainResult r = run_chain(copy, eval, positions[si], maxDepth, candK);
            if (!is_valid_permutation(copy) || full_route_cost(copy) != copy.fEvaluationValue) {
                cerr << "SANITY FAILURE at start=" << positions[si] << "\n";
                return 1;
            }
            if (r.bestDelta < 0) escapesThisTrial++;
            if (r.bestDelta < trialBestDelta) trialBestDelta = r.bestDelta;
        }

        totalStarts += numStarts;
        totalEscapes += escapesThisTrial;
        if (trialBestDelta < bestDeltaOverall) bestDeltaOverall = trialBestDelta;

        cout << instanceFile << " trial=" << t
             << " n=" << n
             << " base_cost=" << baseCost
             << " starts=" << numStarts
             << " escapes=" << escapesThisTrial
             << " best_delta=" << trialBestDelta
             << " best_delta_pct=" << fixed << setprecision(4)
             << (baseCost > 0 ? 100.0 * trialBestDelta / baseCost : 0.0)
             << "\n";
    }

    cout << "\nSUMMARY " << instanceFile
         << " total_starts=" << totalStarts
         << " total_escapes=" << totalEscapes
         << " escape_pct=" << fixed << setprecision(4)
         << (totalStarts > 0 ? 100.0 * totalEscapes / totalStarts : 0.0)
         << " best_delta_seen=" << bestDeltaOverall
         << "\n";

    return 0;
}
