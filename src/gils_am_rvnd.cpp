#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "rvnd.h"
#include "rvnd_lk.h"

using namespace std;

/* GILS-AM-RVND: same ILS loop as gils_rvnd (construction + RVND + fixed
   double-bridge, I_max/I_ILS), but the construction is Construction_AM
   (edge-frequency-biased greedy randomized construction, see
   algorithms/grasp_am.md and src/grasp_am.cpp) instead of plain greedy
   randomized construction. Built to test whether elite-biased construction
   helps once given the same refinement depth as the GILS-RVND baseline --
   see docs/experiments/grasp-am-large-scale.md for why that comparison
   was missing before (grasp_am has no ILS loop, just one RVND pass per
   restart). */

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

    for (int i = 0; i < n; i++)
        sol.fTour[i] = newTour[i];
}

void perturb(Solution& sol, mt19937& gen) {
    double_bridge_once(sol, gen);
    sol.calculateStructures();
}

/* H12a follow-up: GILS-AM-RVND already ties gils_rvnd's quality while
   being 20-26% faster (grasp-am-large-scale.md) -- unlike grasp_am (no
   ILS loop), it has the same double-bridge+RVND depth as the baseline, so
   it doesn't share the mechanism that made extended-oropt wash out to
   noise there (h12-extended-oropt.md section 11). Testing whether
   extended-oropt's real quality gain (H12a) survives on top of the
   memory-biased construction + speed advantage this binary already has --
   i.e. whether the two independent wins (speed here, quality there)
   compose into something both faster and better than plain gils_rvnd. */
enum class RvndMode { Single, ExtendedOrOpt, ExtendedOrOptWide, LKEscape };

void run_rvnd(RvndMode mode, Solution& sol, Evaluator& eval, mt19937& gen) {
    if (mode == RvndMode::ExtendedOrOpt) RVND_ExtendedOrOpt(sol, gen);
    else if (mode == RvndMode::ExtendedOrOptWide) RVND_ExtendedOrOptWide(sol, gen);
    else if (mode == RvndMode::LKEscape) RVND_LKEscape(sol, eval, gen);
    else RVND(sol, gen);
}

enum class ParentMode { Pool, Pair };

struct EliteSet {
    vector<Solution> sols;
    int maxSize;

    EliteSet(int maxSize_) : maxSize(maxSize_) {}

    void add(const Solution& s) {
        for (const auto& es : sols) {
            if (es.fEvaluationValue != s.fEvaluationValue) continue;
            if (equal(es.fTour, es.fTour + es.fN, s.fTour)) return;
        }

        sols.push_back(s);
        sort(sols.begin(), sols.end(), [](const Solution& a, const Solution& b) {
            return a.fEvaluationValue < b.fEvaluationValue;
        });
        if ((int)sols.size() > maxSize) sols.pop_back();
    }
};

/* Sparse edge "vote" counts, normalized by however many solutions
   contributed them -- the whole elite pool (ParentMode::Pool) or exactly
   two chosen parents (ParentMode::Pair). Same scheme as src/grasp_am.cpp. */
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

void construction_am(Solution& sol, Evaluator& eval, double alpha, const EdgeFreq& freq,
                      double lambda, mt19937& gen) {
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
        for (int d : dists) avgDist += d;
        avgDist /= (double)dists.size();

        for (int node : CL) {
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
        for (const auto& c : candidates)
            if (c.second <= threshold) rcl.push_back(c.first);
        if (rcl.empty()) rcl.push_back(candidates.front().first);

        uniform_int_distribution<int> dist(0, rcl.size() - 1);
        int nextNode = rcl[dist(gen)];

        route.push_back(nextNode);
        current = nextNode;

        CL.erase(find(CL.begin(), CL.end(), nextNode));
    }

    sol.Define(n);
    sol.fDist = eval.fEdgeDis;
    for (int i = 0; i < n; i++) sol.fTour[i] = route[i];
    sol.calculateStructures();
}

void gils_am_rvnd(Solution& bestSol, Evaluator& eval, int I_max, int I_ILS,
                   const vector<double>& R, int poolSize, double lambda,
                   ParentMode parentMode, RvndMode rvndMode, mt19937& gen) {
    int fStar = INT_MAX;
    EliteSet memory(poolSize);

    for (int i = 0; i < I_max; i++) {
        EdgeFreq freq = (parentMode == ParentMode::Pair)
            ? two_parent_frequency(memory, gen)
            : pool_frequency(memory);

        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        Solution s;
        construction_am(s, eval, alpha, freq, lambda, gen);

        Solution sPrime(s);

        int iterILS = 0;
        while (iterILS < I_ILS) {
            run_rvnd(rvndMode, s, eval, gen);

            if (s.fEvaluationValue < sPrime.fEvaluationValue) {
                sPrime = s;
                iterILS = 0;
            }

            s = sPrime;
            perturb(s, gen);
            iterILS++;
        }

        memory.add(sPrime);

        if (sPrime.fEvaluationValue < fStar) {
            bestSol = sPrime;
            fStar = sPrime.fEvaluationValue;
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./gils_am_rvnd <instance.tsp> [--imax 10] [--iils 100] [--pool 20]\n";
        cerr << "    [--lambda 0.50] [--parent-mode pool|pair]\n";
        cerr << "    [--rvnd-mode single|extended-oropt|extended-oropt-wide|lk-escape] [--seed N]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int I_max = 10;
    int I_ILS = 100;
    int poolSize = 20;
    double lambda = 0.50;
    ParentMode parentMode = ParentMode::Pool;
    RvndMode rvndMode = RvndMode::Single;
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--imax" && i + 1 < argc) {
            I_max = stoi(argv[++i]);
        } else if (a == "--iils" && i + 1 < argc) {
            I_ILS = stoi(argv[++i]);
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
            else if (m == "lk-escape") rvndMode = RvndMode::LKEscape;
            else { cerr << "Unknown --rvnd-mode: " << m << "\n"; return 1; }
        } else if (a == "--seed" && i + 1 < argc) {
            seed = stol(argv[++i]);
        }
    }

    if (poolSize < 1) poolSize = 1;

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    vector<double> R;
    for (double r = 0.0; r <= 0.25; r += 0.01)
        R.push_back(r);

    Solution bestSol;
    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    gils_am_rvnd(bestSol, eval, I_max, I_ILS, R, poolSize, lambda, parentMode, rvndMode, gen);

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "IILS " << I_ILS << "\n";
    cout << "POOL " << poolSize << "\n";
    cout << "LAMBDA " << fixed << setprecision(2) << lambda << "\n";
    cout << "PARENT_MODE " << (parentMode == ParentMode::Pool ? "pool" : "pair") << "\n";
    cout << "RVND_MODE " << (rvndMode == RvndMode::ExtendedOrOpt ? "extended-oropt"
                              : rvndMode == RvndMode::ExtendedOrOptWide ? "extended-oropt-wide"
                              : rvndMode == RvndMode::LKEscape ? "lk-escape" : "single") << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
