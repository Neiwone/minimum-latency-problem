#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* Read-only diagnostic for H12b (genuine 3-opt). Does NOT touch
   solution.cpp/neighborhoods.cpp/rvnd.cpp -- only reads T/C/Cr via the
   same append/appendReversed pattern already used by
   Solution::evaluate2Opt/evaluateOrOpt, chained over 4 blocks instead of
   2-3. Never mutates the Solution passed in.

   3 cuts (i<j<k) split the tour into 4 blocks: A=[0,i], B=[i+1,j],
   C=[j+1,k], D=[k+1,n-1] (A always first since it holds the depot at
   position 0). Of the reconnections of these 4 blocks, the ones already
   reachable by a SINGLE existing neighborhood are:
     - reversing any one contiguous span (B alone, C alone, or B+C as one
       merged span, which equals rev(C)+rev(B) -- i.e. swaps B/C order
       AND reverses each) -- all already covered by neighborhood_2opt,
       since it tries every contiguous [p,q] reversal.
     - relocating a short segment (B or C, length <= current Or-opt max)
       elsewhere -- covered by neighborhood_oropt2/3/4/5/6/8/10 (H12a).

   The reconnection that is NOT reachable by any single existing move:
   reversing B and C INDEPENDENTLY while keeping their original order --
   A + rev(B) + rev(C) + D. (Reversing the merged B+C span gives
   rev(C)+rev(B), a different tour -- order swapped too.) This is the
   textbook "type-7" 3-opt reconnection that only a genuine 3-opt
   neighborhood reaches. This diagnostic measures whether that specific
   move ever improves a fully extended-oropt-converged local optimum. */

int delta_double_reversal(const Solution& sol, int i, int j, int k) {
    int n = sol.fN;
    int t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = sol.T[u][v];
        int Cu = sol.C[u][v];
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
        int Tu = sol.T[u][v];
        int Cu = sol.Cr[u][v];
        int Wu = sol.getW(u, v);
        int firstNode = sol.fTour[v];
        int lastNode  = sol.fTour[u];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = sol.fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    append(0, i);              // A
    appendReversed(i + 1, j);  // rev(B)
    appendReversed(j + 1, k);  // rev(C)
    append(k + 1, n - 1);      // D

    return c - sol.fEvaluationValue;
}

struct ScanResult {
    long triplesTested = 0;
    long improving = 0;
    int bestDelta = 0;
};

ScanResult scan_double_reversal(const Solution& sol) {
    int n = sol.fN;
    ScanResult res;
    for (int i = 1; i < n - 2; i++) {
        for (int j = i + 1; j < n - 1; j++) {
            for (int k = j + 1; k < n; k++) {
                int d = delta_double_reversal(sol, i, j, k);
                res.triplesTested++;
                if (d < 0) res.improving++;
                if (d < res.bestDelta) res.bestDelta = d;
            }
        }
    }
    return res;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: ./diag_3opt <instance.tsp> [--seed N] [--trials T]\n";
        return 1;
    }

    string instanceFile = argv[1];
    long seed = -1;
    int trials = 5;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
        else if (a == "--trials" && i + 1 < argc) trials = stoi(argv[++i]);
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    for (int t = 0; t < trials; t++) {
        Solution s;
        construction(s, eval, 0.15, gen);
        RVND_ExtendedOrOpt(s, gen); // strongest baseline available (H12a)

        auto t0 = chrono::high_resolution_clock::now();
        ScanResult r = scan_double_reversal(s);
        auto t1 = chrono::high_resolution_clock::now();
        double scan_ms = chrono::duration<double, milli>(t1 - t0).count();

        cout << instanceFile << " trial=" << t
             << " base_cost=" << s.fEvaluationValue
             << " triples=" << r.triplesTested
             << " improving=" << r.improving
             << " best_delta=" << r.bestDelta
             << " best_delta_pct=" << fixed << setprecision(4)
             << (100.0 * r.bestDelta / s.fEvaluationValue)
             << " scan_ms=" << fixed << setprecision(0) << scan_ms
             << "\n";
    }

    return 0;
}
