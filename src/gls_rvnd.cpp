#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* H11: Guided Local Search (Voudouris & Tsang, 1997). Changes WHAT the search
   climbs: converged edges get penalized in a guide matrix RVND reruns on. */

/* True cost is tracked separately -- this only swaps Solution::fDist. */

int full_route_cost(const int* tour, int n, int** dist) {
    int t = 0, total = 0;
    for (int i = 1; i < n; i++) {
        t += dist[tour[i - 1]][tour[i]];
        total += t;
    }
    return total;
}

/* Plain GLS plateaus hard (identical best cost from 3k to 13k iterations),
   so --kick-every N adds a double-bridge on top of the guided reconvergence. */
void double_bridge_once(Solution& sol, mt19937& gen) {
    int n = sol.fN;
    if (n < 8) return;

    vector<int> cuts;
    uniform_int_distribution<int> dist(1, n - 2);
    while ((int)cuts.size() < 3) {
        int c = dist(gen);
        bool dup = false;
        for (int x : cuts) if (x == c) { dup = true; break; }
        if (!dup) cuts.push_back(c);
    }
    sort(cuts.begin(), cuts.end());
    int p1 = cuts[0], p2 = cuts[1], p3 = cuts[2];

    vector<int> newTour;
    newTour.reserve(n);
    for (int i = 0;  i < p1; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p2; i < p3; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p1; i < p2; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p3; i < n;  i++) newTour.push_back(sol.fTour[i]);
    for (int i = 0; i < n; i++) sol.fTour[i] = newTour[i];
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./gls_rvnd <instance.tsp> [--iterations 300] [--lambda-alpha 0.3]\n";
        cerr << "    [--construction-alpha 0.15] [--kick-every 0] [--seed N]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int iterations = 300;
    double lambdaAlpha = 0.3;
    double constructionAlpha = 0.15;
    int kickEvery = 0; // 0 = disabled, matches original GLS-only behavior
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--iterations" && i + 1 < argc) iterations = stoi(argv[++i]);
        else if (a == "--lambda-alpha" && i + 1 < argc) lambdaAlpha = stod(argv[++i]);
        else if (a == "--construction-alpha" && i + 1 < argc) constructionAlpha = stod(argv[++i]);
        else if (a == "--kick-every" && i + 1 < argc) kickEvery = stoi(argv[++i]);
        else if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());
    int n = eval.Ncity;
    int** trueDist = eval.fEdgeDis;

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    // guideDist starts as an exact copy of the true distances (no penalty yet)
    vector<vector<int>> guideDistStorage(n, vector<int>(n));
    vector<int*> guideDist(n);
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) guideDistStorage[i][j] = trueDist[i][j];
        guideDist[i] = guideDistStorage[i].data();
    }

    vector<vector<int>> penalty(n, vector<int>(n, 0));

    Solution s;
    construction(s, eval, constructionAlpha, gen); // s.fDist = trueDist here
    RVND(s, gen);

    int bestCost = s.fEvaluationValue; // real cost -- fDist was trueDist for this pass
    vector<int> bestTour(s.fTour, s.fTour + n);

    // classic GLS heuristic: lambda ~ fraction of the average edge's
    // contribution to the cost of the first local optimum found
    double lambda = lambdaAlpha * (double)bestCost / max(1, n - 1);

    int improvingIters = 0;

    for (int iter = 0; iter < iterations; iter++) {
        if (kickEvery > 0 && iter > 0 && iter % kickEvery == 0)
            double_bridge_once(s, gen);

        for (int i = 0; i < n; i++)
            for (int j = 0; j < n; j++)
                guideDist[i][j] = trueDist[i][j] + (int)llround(lambda * penalty[i][j]);

        s.fDist = guideDist.data();
        s.calculateStructures();
        RVND(s, gen);

        int realCost = full_route_cost(s.fTour, n, trueDist);
        if (realCost < bestCost) {
            bestCost = realCost;
            bestTour.assign(s.fTour, s.fTour + n);
            improvingIters++;
        }

        // penalize the single highest-utility edge in the CURRENT tour
        // (utility = real edge cost / (1 + times already penalized) --
        // favors expensive, rarely-penalized edges, classic GLS choice)
        int bu = -1, bv = -1;
        double bestUtil = -1.0;
        for (int k = 0; k < n - 1; k++) {
            int u = s.fTour[k], v = s.fTour[k + 1];
            double util = (double)trueDist[u][v] / (1.0 + penalty[u][v]);
            if (util > bestUtil) { bestUtil = util; bu = u; bv = v; }
        }
        penalty[bu][bv] += 1;
        penalty[bv][bu] += 1;
    }

    Solution finalSol;
    finalSol.Define(n);
    finalSol.fDist = trueDist;
    for (int i = 0; i < n; i++) finalSol.fTour[i] = bestTour[i];
    finalSol.calculateStructures();

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << finalSol.fN << "\n";
    cout << "COST " << finalSol.fEvaluationValue << "\n";
    cout << "ITERATIONS " << iterations << "\n";
    cout << "IMPROVING_ITERS " << improvingIters << "\n";
    cout << "LAMBDA " << fixed << setprecision(4) << lambda << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < finalSol.fN; i++)
        cout << finalSol.fTour[i] << ",\n"[i == finalSol.fN - 1];

    return 0;
}
