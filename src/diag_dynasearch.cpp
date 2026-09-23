#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* Read-only probe for H10: TSP 2-opt gains are additive over disjoint moves,
   MLP's may not be -- do non-improving PAIRS ever improve together? */

int full_route_cost(const vector<int>& tour, int** dist) {
    int n = (int)tour.size();
    int t = 0, total = 0;
    for (int i = 1; i < n; i++) {
        t += dist[tour[i - 1]][tour[i]];
        total += t;
    }
    return total;
}

/* Solution::evaluate2Opt's computation, returning the signed delta instead
   of a boolean. Read-only. */
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

    return c - sol.fEvaluationValue;
}

struct Candidate { int i, j, delta; };

struct DiagResult {
    long pairsTested = 0;
    long pairsImproving = 0;
    int bestCombinedDelta = 0;   // most negative found (0 if none improving)
    long nonAdditivePairs = 0;   // combinedDelta != delta_i + delta_j
    double meanInteraction = 0;  // mean(combinedDelta - (delta_i+delta_j))
};

DiagResult run_diagnostic(Solution& sol, int poolSize) {
    int n = sol.fN;

    vector<Candidate> all;
    all.reserve((size_t)n * n / 2);
    for (int i = 1; i < n; i++)
        for (int j = i + 1; j < n; j++)
            all.push_back({i, j, delta_2opt(sol, i, j)});

    sort(all.begin(), all.end(), [](const Candidate& a, const Candidate& b) {
        return a.delta < b.delta;
    });

    int K = min((int)all.size(), poolSize);
    vector<Candidate> pool(all.begin(), all.begin() + K);

    vector<int> baseTour(sol.fTour, sol.fTour + n);
    int baseCost = sol.fEvaluationValue;

    DiagResult res;
    double interactionSum = 0.0;

    for (int a = 0; a < K; a++) {
        for (int b = a + 1; b < K; b++) {
            const Candidate& A = pool[a];
            const Candidate& B = pool[b];
            // require strict disjointness of the reversed index ranges
            if (!(A.j < B.i || B.j < A.i)) continue;

            vector<int> tour = baseTour;
            reverse(tour.begin() + A.i, tour.begin() + A.j + 1);
            reverse(tour.begin() + B.i, tour.begin() + B.j + 1);

            int combinedCost = full_route_cost(tour, sol.fDist);
            int combinedDelta = combinedCost - baseCost;
            int additiveDelta = A.delta + B.delta;

            res.pairsTested++;
            if (combinedDelta < 0) res.pairsImproving++;
            if (combinedDelta < res.bestCombinedDelta) res.bestCombinedDelta = combinedDelta;
            if (combinedDelta != additiveDelta) res.nonAdditivePairs++;
            interactionSum += (combinedDelta - additiveDelta);
        }
    }

    if (res.pairsTested > 0) res.meanInteraction = interactionSum / res.pairsTested;
    return res;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage: ./diag_dynasearch <instance.tsp> [--seed N] [--trials T] [--pool K]\n";
        return 1;
    }

    string instanceFile = argv[1];
    long seed = -1;
    int trials = 5;
    int poolSize = 120;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
        else if (a == "--trials" && i + 1 < argc) trials = stoi(argv[++i]);
        else if (a == "--pool" && i + 1 < argc) poolSize = stoi(argv[++i]);
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    long totalPairs = 0, totalImproving = 0, totalNonAdditive = 0;
    int worstBest = 0;
    double interactionAccum = 0.0;

    for (int t = 0; t < trials; t++) {
        Solution s;
        construction(s, eval, 0.15, gen);
        RVND(s, gen);

        DiagResult r = run_diagnostic(s, poolSize);

        cout << instanceFile << " trial=" << t
             << " base_cost=" << s.fEvaluationValue
             << " pairs_tested=" << r.pairsTested
             << " pairs_improving=" << r.pairsImproving
             << " best_combined_delta=" << r.bestCombinedDelta
             << " non_additive_pairs=" << r.nonAdditivePairs
             << " mean_interaction=" << fixed << setprecision(3) << r.meanInteraction
             << "\n";

        totalPairs += r.pairsTested;
        totalImproving += r.pairsImproving;
        totalNonAdditive += r.nonAdditivePairs;
        if (r.bestCombinedDelta < worstBest) worstBest = r.bestCombinedDelta;
        interactionAccum += r.meanInteraction;
    }

    cout << "\nSUMMARY " << instanceFile
         << " total_pairs=" << totalPairs
         << " total_improving=" << totalImproving
         << " improving_pct=" << fixed << setprecision(4)
         << (totalPairs > 0 ? 100.0 * totalImproving / totalPairs : 0.0)
         << " total_non_additive=" << totalNonAdditive
         << " non_additive_pct=" << (totalPairs > 0 ? 100.0 * totalNonAdditive / totalPairs : 0.0)
         << " best_combined_delta_seen=" << worstBest
         << " mean_interaction_avg=" << (trials > 0 ? interactionAccum / trials : 0.0)
         << "\n";

    return 0;
}
