#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "rvnd.h"

using namespace std;

struct StepTimings {
    double construction_ms = 0;
    double rvnd_ms = 0;
    double total_ms = 0;
};

struct EliteSet {
    vector<Solution> sols;
    int maxSize;
    vector<vector<int>> freq; // freq[i][j] = number of elite tours containing edge (i,j)

    EliteSet(int n, int max_size) : maxSize(max_size) {
        freq.assign(n, vector<int>(n, 0));
    }

    void add(const Solution& s) {
        // Check for duplicates
        for (const auto& es : sols) {
            if (es.fEvaluationValue == s.fEvaluationValue) {
                bool same = true;
                for(int i = 0; i < s.fN; i++) {
                    if (es.fTour[i] != s.fTour[i]) {
                        same = false;
                        break;
                    }
                }
                if (same) return;
            }
        }

        sols.push_back(s);
        sort(sols.begin(), sols.end(), [](const Solution& a, const Solution& b){
            return a.fEvaluationValue < b.fEvaluationValue;
        });

        if ((int)sols.size() > maxSize) {
            sols.pop_back();
        }

        // Recompute freq
        int n = s.fN;
        freq.assign(n, vector<int>(n, 0));
        for (const auto& es : sols) {
            for (int i = 0; i < n - 1; i++) {
                freq[es.fTour[i]][es.fTour[i+1]]++;
            }
        }
    }
};

static double normalized_edge_frequency(const EliteSet& memory, int u, int v) {
    if (memory.sols.empty())
        return 0.0;
    return (double)memory.freq[u][v] / (double)memory.sols.size();
}

void construction_am(Solution& sol, Evaluator& eval, double alpha, EliteSet& memory, double lambda, mt19937& gen) {
    int n = eval.Ncity;

    double alphaClamped = max(0.0, min(alpha, 1.0));
    double lambdaClamped = max(0.0, lambda);

    vector<int> CL;
    for (int i = 1; i < n; i++) CL.push_back(i);

    vector<int> route;
    route.push_back(0);
    int current = 0;

    while (!CL.empty()) {
        vector<pair<int, double>> candidates;
        vector<int> dists;
        double minCost = numeric_limits<double>::max();
        double maxCost = numeric_limits<double>::lowest();

        dists.reserve(CL.size());
        for (int node : CL)
            dists.push_back(eval.fEdgeDis[current][node]);

        double avgDist = 0.0;
        for (int d : dists)
            avgDist += d;
        avgDist /= (double)dists.size();

        for (int node : CL) {
            // Adaptive Memory cost adjustment
            double origDist = eval.fEdgeDis[current][node];
            double freqNorm = normalized_edge_frequency(memory, current, node);
            double bonus = lambdaClamped * freqNorm * avgDist;
            double pseudoCost = origDist - bonus;

            candidates.push_back({node, pseudoCost});
            if (pseudoCost < minCost) minCost = pseudoCost;
            if (pseudoCost > maxCost) maxCost = pseudoCost;
        }

        sort(candidates.begin(), candidates.end(), [](const auto& a, const auto& b) {
            return a.second < b.second;
        });

        double threshold = minCost + alphaClamped * (maxCost - minCost);
        vector<int> rcl;
        for (const auto& c : candidates) {
            if (c.second <= threshold) {
                rcl.push_back(c.first);
            }
        }
        if (rcl.empty()) {
            rcl.push_back(candidates.front().first);
        }

        uniform_int_distribution<int> dist(0, rcl.size() - 1);
        int nextNode = rcl[dist(gen)];

        route.push_back(nextNode);
        current = nextNode;

        auto it = find(CL.begin(), CL.end(), nextNode);
        CL.erase(it);
    }

    sol.Define(n);
    sol.fDist = eval.fEdgeDis;
    for (int i = 0; i < n; i++) sol.fTour[i] = route[i];
    sol.calculateStructures();
}

void grasp_am(
    Solution& bestSol,
    Evaluator& eval,
    int maxIter,
    optional<double> fixedAlpha,
    int poolSize,
    double lambda,
    bool verbose,
    StepTimings* timings
) {
    random_device rd;
    mt19937 gen(rd());
    using Clock = chrono::high_resolution_clock;

    vector<double> R;
    for (double r = 0.00; r <= 0.25; r += 0.01) R.push_back(r);

    int bestIter = -1;
    int bestCost = INT_MAX;
    double totalConstructionMs = 0.0;
    double totalRvndMs = 0.0;

    EliteSet memory(eval.Ncity, poolSize);

    for (int iter = 0; iter < maxIter; iter++) {
        double alpha = 0.0;
        if (!fixedAlpha.has_value() && iter == 0) {
            alpha = 0.0;
        } else if (fixedAlpha.has_value()) {
            alpha = fixedAlpha.value();
        } else {
            uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
            alpha = R[rDist(gen)];
        }

        auto tc0 = Clock::now();
        Solution s;
        construction_am(s, eval, alpha, memory, lambda, gen);
        auto tc1 = Clock::now();
        double constructionMs = chrono::duration<double, milli>(tc1 - tc0).count();
        totalConstructionMs += constructionMs;

        auto tr0 = Clock::now();
        RVND(s, gen);
        auto tr1 = Clock::now();
        double rvndMs = chrono::duration<double, milli>(tr1 - tr0).count();
        totalRvndMs += rvndMs;

        memory.add(s);

        if (verbose) {
            cerr << "  iter " << iter
                 << ": alpha=" << fixed << setprecision(2) << alpha
                 << "  constr=" << setprecision(1) << constructionMs << "ms"
                 << "  rvnd=" << rvndMs << "ms"
                 << "  cost=" << s.fEvaluationValue << "\n";
        }

        if (s.fEvaluationValue < bestCost) {
            bestCost = s.fEvaluationValue;
            bestSol = s;
            bestIter = iter;
        }
    }

    if (timings) {
        timings->construction_ms = totalConstructionMs;
        timings->rvnd_ms = totalRvndMs;
    }

    if (verbose) {
        cerr << "best at iter " << bestIter << " cost=" << bestCost << "\n";
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./grasp_am <instance.tsp> [--iter 800] [--alpha 0.15] [--pool 20] [--lambda 0.50] [-v]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int maxIter = 800;
    optional<double> alpha;
    int poolSize = 20;
    double lambda = 0.50; // Multiplier for normalized adaptive-memory bonus
    bool verbose = false;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if ((a == "--iter" || a == "--imax") && i + 1 < argc) {
            maxIter = stoi(argv[++i]);
        } else if (a == "--alpha" && i + 1 < argc) {
            alpha = stod(argv[++i]);
        } else if (a == "--pool" && i + 1 < argc) {
            poolSize = stoi(argv[++i]);
        } else if (a == "--lambda" && i + 1 < argc) {
            lambda = stod(argv[++i]);
        } else if (a == "--verbose" || a == "-v") {
            verbose = true;
        }
    }

    if (poolSize < 1) poolSize = 1;
    if (maxIter < 1) maxIter = 1;

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    Solution bestSol;
    StepTimings timings;

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    grasp_am(bestSol, eval, maxIter, alpha, poolSize, lambda, verbose, &timings);

    auto t1 = Clock::now();
    double runtimeMs = chrono::duration<double, milli>(t1 - t0).count();
    timings.total_ms = runtimeMs;

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "ITER " << maxIter << "\n";
    cout << "POOL " << poolSize << "\n";
    cout << "LAMBDA " << fixed << setprecision(2) << lambda << "\n";
    if (alpha.has_value())
        cout << "ALPHA " << fixed << setprecision(2) << alpha.value() << "\n";
    else
        cout << "ALPHA randomized(0.00..0.25)\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtimeMs << "\n";
    cout << "CONSTRUCTION_MS " << fixed << setprecision(3) << timings.construction_ms << "\n";
    cout << "RVND_MS " << fixed << setprecision(3) << timings.rvnd_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
