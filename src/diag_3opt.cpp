#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* Read-only probe for H12b: does A + rev(B) + rev(C) + D -- the one 3-opt
   reconnection no single 2-opt or or-opt reaches -- ever improve? */

Cost delta_double_reversal(const Solution& sol, int i, int j, int k) {
    int n = sol.fN;
    Cost t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = sol.getT(u, v);
        Cost Cu = sol.getC(u, v);
        int Wu = sol.getW(u, v);
        int firstNode = sol.fTour[u];
        int lastNode  = sol.fTour[v];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        Cost e = sol.fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    auto appendReversed = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = sol.getT(u, v);
        Cost Cu = sol.getCr(u, v);
        int Wu = sol.getW(u, v);
        int firstNode = sol.fTour[v];
        int lastNode  = sol.fTour[u];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        Cost e = sol.fDist[last][firstNode];
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
    Cost bestDelta = 0;
};

ScanResult scan_double_reversal(const Solution& sol) {
    int n = sol.fN;
    ScanResult res;
    for (int i = 1; i < n - 2; i++) {
        for (int j = i + 1; j < n - 1; j++) {
            for (int k = j + 1; k < n; k++) {
                Cost d = delta_double_reversal(sol, i, j, k);
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
