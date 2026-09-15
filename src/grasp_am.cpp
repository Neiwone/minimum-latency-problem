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

enum class ParentMode { Pool, Pair };

/* Sparse edge votes, normalized by however many solutions contributed:
   importance(u,v) = how many "parents" agree on that edge. */
struct EdgeFreq {
    unordered_map<long long, int> counts;
    int normalizer = 0;

    static long long key(int u, int v) { return (long long)u * 100000LL + v; }

    void add_tour(const int* tour, int n) {
        for (int i = 0; i + 1 < n; i++)
            counts[key(tour[i], tour[i + 1])]++;
    }

    double normalized(int u, int v) const {
        if (normalizer == 0) return 0.0;
        auto it = counts.find(key(u, v));
        return it == counts.end() ? 0.0 : (double)it->second / normalizer;
    }
};

EdgeFreq pool_frequency(const EliteSet& memory) {
    EdgeFreq ef;
    ef.normalizer = (int)memory.sols.size();
    for (const auto& s : memory.sols)
        ef.add_tour(s.fTour, s.fN);
    return ef;
}

/* Importance from two random elites only -- greedy crossover (Grefenstette
   et al., 1985) rather than pool-wide frequency. */
EdgeFreq two_parent_frequency(const EliteSet& memory, mt19937& gen) {
    EdgeFreq ef;
    int k = (int)memory.sols.size();
    if (k == 0) return ef;

    if (k == 1) {
        ef.normalizer = 1;
        ef.add_tour(memory.sols[0].fTour, memory.sols[0].fN);
        return ef;
    }

    uniform_int_distribution<int> d(0, k - 1);
    int a = d(gen);
    int b = d(gen);
    while (b == a) b = d(gen);

    ef.normalizer = 2;
    ef.add_tour(memory.sols[a].fTour, memory.sols[a].fN);
    ef.add_tour(memory.sols[b].fTour, memory.sols[b].fN);
    return ef;
}

void construction_am(Solution& sol, Evaluator& eval, double alpha, const EdgeFreq& freq, double lambda, mt19937& gen) {
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
            double freqNorm = freq.normalized(current, node);
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

/* grasp_am does ONE convergence per iteration, so its weakness is depth,
   not the memory bias -- a stronger RVND may close part of that gap. */
enum class RvndMode { Single, ExtendedOrOpt, ExtendedOrOptWide };

void run_rvnd(RvndMode mode, Solution& sol, mt19937& gen) {
    if (mode == RvndMode::ExtendedOrOpt) RVND_ExtendedOrOpt(sol, gen);
    else if (mode == RvndMode::ExtendedOrOptWide) RVND_ExtendedOrOptWide(sol, gen);
    else RVND(sol, gen);
}

void grasp_am(
    Solution& bestSol,
    Evaluator& eval,
    int maxIter,
    optional<double> fixedAlpha,
    int poolSize,
    double lambda,
    ParentMode parentMode,
    RvndMode rvndMode,
    bool verbose,
    StepTimings* timings,
    mt19937& gen
) {
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

        EdgeFreq freq = (parentMode == ParentMode::Pair)
            ? two_parent_frequency(memory, gen)
            : pool_frequency(memory);

        auto tc0 = Clock::now();
        Solution s;
        construction_am(s, eval, alpha, freq, lambda, gen);
        auto tc1 = Clock::now();
        double constructionMs = chrono::duration<double, milli>(tc1 - tc0).count();
        totalConstructionMs += constructionMs;

        auto tr0 = Clock::now();
        run_rvnd(rvndMode, s, gen);
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
        cerr << "  ./grasp_am <instance.tsp> [--iter 800] [--alpha 0.15] [--pool 20] [--lambda 0.50]\n";
        cerr << "    [--parent-mode pool|pair] [--rvnd-mode single|extended-oropt|extended-oropt-wide]\n";
        cerr << "    [--seed N] [-v]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int maxIter = 800;
    optional<double> alpha;
    int poolSize = 20;
    double lambda = 0.50; // Multiplier for normalized adaptive-memory bonus
    ParentMode parentMode = ParentMode::Pool;
    RvndMode rvndMode = RvndMode::Single;
    bool verbose = false;
    long seed = -1;

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
        } else if (a == "--parent-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "pool") parentMode = ParentMode::Pool;
            else if (m == "pair") parentMode = ParentMode::Pair;
            else { cerr << "Unknown --parent-mode: " << m << "\n"; return 1; }
        } else if (a == "--rvnd-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "single") rvndMode = RvndMode::Single;
            else if (m == "extended-oropt") rvndMode = RvndMode::ExtendedOrOpt;
            else if (m == "extended-oropt-wide") rvndMode = RvndMode::ExtendedOrOptWide;
            else { cerr << "Unknown --rvnd-mode: " << m << "\n"; return 1; }
        } else if (a == "--seed" && i + 1 < argc) {
            seed = stol(argv[++i]);
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
    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    grasp_am(bestSol, eval, maxIter, alpha, poolSize, lambda, parentMode, rvndMode, verbose, &timings, gen);

    auto t1 = Clock::now();
    double runtimeMs = chrono::duration<double, milli>(t1 - t0).count();
    timings.total_ms = runtimeMs;

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "ITER " << maxIter << "\n";
    cout << "POOL " << poolSize << "\n";
    cout << "LAMBDA " << fixed << setprecision(2) << lambda << "\n";
    cout << "PARENT_MODE " << (parentMode == ParentMode::Pool ? "pool" : "pair") << "\n";
    cout << "RVND_MODE " << (rvndMode == RvndMode::ExtendedOrOpt ? "extended-oropt"
                              : rvndMode == RvndMode::ExtendedOrOptWide ? "extended-oropt-wide" : "single") << "\n";
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
