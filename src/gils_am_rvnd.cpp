#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "rvnd.h"
#include "rvnd_lk.h"
#include "rvnd_adaptive.h"
#include "neighborhoods_cand.h"

using namespace std;

/* Double bridge, returning the position range it disturbed so the ILS can
   re-arm just that span. maxSeg/frontBias measured worse, off by default. */
pair<int,int> double_bridge_once(Solution& sol, mt19937& gen, int maxSeg, double frontBias) {
    int n = sol.fN;
    if (n < 8) return {-1, -1};

    int p1, p2, p3;

    if (maxSeg > 0) {
        int cap = min(maxSeg, (n - 2) / 2);
        if (cap < 1) cap = 1;

        uniform_int_distribution<int> segDist(1, cap);
        int s1 = segDist(gen);
        int s2 = segDist(gen);

        int span = s1 + s2;
        if (span > n - 2) return {-1, -1};

        int hi = n - 1 - span;
        if (frontBias > 1.0) {   /* note: only reachable when maxSeg > 0 */
            uniform_real_distribution<double> u01(0.0, 1.0);
            double u = pow(u01(gen), frontBias);
            p1 = 1 + (int)(u * (double)hi);
            if (p1 > hi) p1 = hi;
            if (p1 < 1)  p1 = 1;
        } else {
            uniform_int_distribution<int> startDist(1, hi);
            p1 = startDist(gen);
        }
        p2 = p1 + s1;
        p3 = p2 + s2;
    } else {
        vector<int> cuts;
        uniform_int_distribution<int> dist(1, n - 2);

        while ((int)cuts.size() < 3) {
            int c = dist(gen);
            bool dup = false;
            for (int x : cuts) if (x == c) { dup = true; break; }
            if (!dup) cuts.push_back(c);
        }
        sort(cuts.begin(), cuts.end());

        p1 = cuts[0]; p2 = cuts[1]; p3 = cuts[2];
    }

    vector<int> newTour;
    newTour.reserve(n);

    for (int i = 0;  i < p1; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p2; i < p3; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p1; i < p2; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p3; i < n;  i++) newTour.push_back(sol.fTour[i]);

    for (int i = 0; i < n; i++)
        sol.fTour[i] = newTour[i];

    return {p1, p3 - 1};
}

pair<int,int> perturb(Solution& sol, mt19937& gen, int dbMaxSeg, double frontBias) {
    auto range = double_bridge_once(sol, gen, dbMaxSeg, frontBias);
    sol.calculateStructures();
    return range;
}

enum class RvndMode { Single, ExtendedOrOpt, ExtendedOrOptWide, ExtendedOrOptRev, Candidate,
                      CandidateDLB, LKEscape, AdaptiveOrOpt };

/* Candidate-list configuration, set once per run from the CLI. */
static CandList g_cand;
static int  g_candMaxLen  = 6;
static bool g_candReversed = true;

/* `adaptState` and `dlb` must live across the whole run, not per call. */
void run_rvnd(RvndMode mode, Solution& sol, Evaluator& eval, mt19937& gen,
              AdaptiveOrOptState& adaptState, DlbState& dlb) {
    if (mode == RvndMode::CandidateDLB) RVND_CandidateDLB(sol, g_cand, g_candMaxLen, g_candReversed, gen, dlb);
    else if (mode == RvndMode::ExtendedOrOpt) RVND_ExtendedOrOpt(sol, gen);
    else if (mode == RvndMode::ExtendedOrOptWide) RVND_ExtendedOrOptWide(sol, gen);
    else if (mode == RvndMode::ExtendedOrOptRev) RVND_ExtendedOrOptRev(sol, gen);
    else if (mode == RvndMode::Candidate) RVND_Candidate(sol, g_cand, g_candMaxLen, g_candReversed, gen);
    else if (mode == RvndMode::LKEscape) RVND_LKEscape(sol, eval, gen);
    else if (mode == RvndMode::AdaptiveOrOpt) RVND_AdaptiveOrOpt(sol, gen, adaptState);
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

    /* The RCL is a threshold set, so sorting the candidates changed
       nothing about which ones pass -- dropped, leaving this O(n^2). */
    vector<pair<int, double>> candidates;
    vector<int> rcl;

    while (!CL.empty()) {
        double minCost = numeric_limits<double>::max();
        double maxCost = numeric_limits<double>::lowest();

        double avgDist = 0.0;
        for (int node : CL) avgDist += eval.fEdgeDis[current][node];
        avgDist /= (double)CL.size();

        candidates.clear();
        for (int node : CL) {
            double origDist = eval.fEdgeDis[current][node];
            double freqNorm = freq.normalized(current, node);
            double bonus = lambdaClamped * freqNorm * avgDist;
            double pseudoCost = origDist - bonus;

            candidates.push_back({node, pseudoCost});
            if (pseudoCost < minCost) minCost = pseudoCost;
            if (pseudoCost > maxCost) maxCost = pseudoCost;
        }

        double threshold = minCost + alphaClamped * (maxCost - minCost);
        rcl.clear();
        for (const auto& c : candidates)
            if (c.second <= threshold) rcl.push_back(c.first);

        if (rcl.empty()) {
            int best = candidates.front().first;
            double bestCost = candidates.front().second;
            for (const auto& c : candidates)
                if (c.second < bestCost) { bestCost = c.second; best = c.first; }
            rcl.push_back(best);
        }

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


/* Arc-based crossover (Ren, Hao, Wu & Fu, EJOR 304(2), 2023): keep the arcs
   both parents agree on, graft a `rate` fraction of the rest. Off by default. */
void crossover_abx(Solution& child, const Solution& A, const Solution& B,
                   mt19937& gen, double rate) {
    const int n = A.fN;
    child = A;

    vector<int> succA(n, -1), succB(n, -1), pos(n, 0);
    for (int i = 0; i + 1 < n; i++) succA[A.fTour[i]] = A.fTour[i + 1];
    for (int i = 0; i + 1 < n; i++) succB[B.fTour[i]] = B.fTour[i + 1];
    for (int i = 0; i < n; i++) pos[child.fTour[i]] = i;

    vector<char> fixed(n, 0);
    for (int c = 0; c < n; c++)
        if (succA[c] != -1 && succA[c] == succB[c]) {
            fixed[c] = 1;
            fixed[succA[c]] = 1;
        }

    vector<pair<int,int>> graft;
    for (int c = 0; c < n; c++)
        if (succB[c] != -1 && succB[c] != succA[c])
            graft.push_back({c, succB[c]});

    shuffle(graft.begin(), graft.end(), gen);
    int take = (int)(graft.size() * rate);

    const int depot = child.fTour[0];
    for (int g = 0; g < take; g++) {
        int u = graft[g].first, v = graft[g].second;
        if (fixed[u] || fixed[v]) continue;
        if (v == depot) continue;

        int pu = pos[u], pv = pos[v];
        if (pv == pu + 1) { fixed[u] = fixed[v] = 1; continue; }

        if (pv > pu) {
            rotate(child.fTour + pu + 1, child.fTour + pv, child.fTour + pv + 1);
            for (int i = pu + 1; i <= pv; i++) pos[child.fTour[i]] = i;
        } else {
            rotate(child.fTour + pv, child.fTour + pv + 1, child.fTour + pu + 1);
            for (int i = pv; i <= pu; i++) pos[child.fTour[i]] = i;
        }
        fixed[u] = fixed[v] = 1;
    }

    child.calculateStructures();
}

/* Reported so a fixed-time run can show the restart-boundary mechanisms
   were exercised at all. */
long g_restarts = 0;
long g_crossovers = 0;

void gils_am_rvnd(Solution& bestSol, Evaluator& eval, int I_max, int I_ILS,
                   const vector<double>& R, int poolSize, double lambda,
                   ParentMode parentMode, RvndMode rvndMode, mt19937& gen,
                   AdaptiveOrOptState& adaptState, double maxTimeSec, int dbMaxSeg,
                   double dbFrontBias, double acceptEps, bool polishOnBest,
                   double abxRate, int restartKick) {
    DlbState dlb;
    int fStar = INT_MAX;
    EliteSet memory(poolSize);

    /* Wall-clock stop, checked between ILS iterations and restarts, so
       the budget can overshoot by at most one RVND convergence. */
    using SteadyClock = chrono::steady_clock;
    const auto tStart = SteadyClock::now();
    const bool timed = maxTimeSec > 0.0;
    auto outOfTime = [&]() {
        if (!timed) return false;
        return chrono::duration<double>(SteadyClock::now() - tStart).count() >= maxTimeSec;
    };

    for (int i = 0; i < I_max; i++) {
        if (outOfTime()) break;
        g_restarts++;

        EdgeFreq freq = (parentMode == ParentMode::Pair)
            ? two_parent_frequency(memory, gen)
            : pool_frequency(memory);

        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        Solution s;
        if (restartKick > 0 && fStar < INT_MAX) {
            /* Soft restart: kick the incumbent instead of throwing it
               away for a fresh construction. Measured worse. */
            s = bestSol;
            for (int k = 0; k < restartKick; k++)
                perturb(s, gen, dbMaxSeg, dbFrontBias);
        } else if (abxRate > 0.0 && (int)memory.sols.size() >= 2) {
            uniform_int_distribution<int> d(0, (int)memory.sols.size() - 1);
            int a = d(gen), b = d(gen);
            while (b == a) b = d(gen);
            crossover_abx(s, memory.sols[a], memory.sols[b], gen, abxRate);
            g_crossovers++;
        } else {
            construction_am(s, eval, alpha, freq, lambda, gen);
        }

        /* A fresh construction is nowhere near a local optimum: arm
           everything. Only perturbations get the cheap partial re-arm. */
        dlb.reset(s.fN);

        Solution sPrime(s);

        int iterILS = 0;
        while (iterILS < I_ILS) {
            run_rvnd(rvndMode, s, eval, gen, adaptState, dlb);

            if (s.fEvaluationValue < sPrime.fEvaluationValue) {
                sPrime = s;
                iterILS = 0;
            }

            if (outOfTime()) break;

            /* acceptEps = 0 is GILS-RVND's strict descent; > 0 is
               threshold acceptance, measured worse. */
            if (!(acceptEps > 0.0 &&
                  (double)s.fEvaluationValue <
                      (double)sPrime.fEvaluationValue * (1.0 + acceptEps)))
                s = sPrime;

            auto hit = perturb(s, gen, dbMaxSeg, dbFrontBias);
            if (hit.first >= 0) dlb.arm_range(s, hit.first - 1, hit.second + 1);
            else dlb.reset(s.fN);
            iterILS++;
        }

        memory.add(sPrime);

        if (sPrime.fEvaluationValue < fStar) {
            /* Two-level VND: the full unpruned RVND buys back the depth
               the pruning gave away. Measured worse. */
            if (polishOnBest) {
                RVND_ExtendedOrOptRev(sPrime, gen);
                if (sPrime.fEvaluationValue < s.fEvaluationValue) {
                    s = sPrime;
                    dlb.reset(s.fN);
                }
            }

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
        cerr << "    [--rvnd-mode single|extended-oropt|extended-oropt-wide|extended-oropt-rev|candidate|candidate-dlb|lk-escape|adaptive-oropt]\n";
    cerr << "    [--cand-k K] [--cand-maxlen L] [--cand-no-rev] [--cand-front F] [--cand-2opt-both]\n";
    cerr << "    [--db-front-bias B]  skew perturbation towards the tour front (1 = uniform)\n";
    cerr << "    [--db-maxseg K]  cap on each swapped double-bridge block (0 = unrestricted)\n";
        cerr << "    [--max-time SECONDS] [--seed N] [-v]\n";
        cerr << "    adaptive-oropt: [--adapt-kstart 6] [--adapt-period 400] [--adapt-rho 0.30]\n";
        cerr << "                    [--adapt-grow 0.10] [--adapt-shrink 0.02]\n";
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
    bool verbose = false;
    double maxTimeSec = -1.0;   /* <=0 disables the time limit */
    int dbMaxSeg = 0;           /* <=0 keeps the unrestricted double bridge */
    int dbMaxSegDiv = 0;        /* >0 sets dbMaxSeg = max(2, n/dbMaxSegDiv) */
    int candK = 12;
    int candFront = 0;          /* extra depot-side or-opt anchors (0 = off) */
    bool cand2optBoth = false;  /* anchor 2-opt on both new edges */
    bool dlbStrict = false;     /* skip (city, neighborhood) pairs already failed */
    double dbFrontBias = 1.0;   /* 1.0 = uniform placement */
    double acceptEps = 0.0;     /* 0 = always walk back to the incumbent */
    bool polishOnBest = false;  /* full unpruned RVND on every new global best */
    double abxRate = 0.0;       /* >0: restarts recombine two elites instead of constructing */
    int restartKick = 0;        /* >0: restarts kick the incumbent instead of constructing */
    bool imaxExplicit = false;
    int    adaptKStart = 6;
    int    adaptPeriod = 400;
    double adaptRho    = 0.30;
    double adaptGrow   = 0.10;
    double adaptShrink = 0.02;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--imax" && i + 1 < argc) {
            I_max = stoi(argv[++i]);
            imaxExplicit = true;
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
        } else if (a == "--db-front-bias" && i + 1 < argc) {
            dbFrontBias = stod(argv[++i]);
        } else if (a == "--cand-k" && i + 1 < argc) {
            candK = stoi(argv[++i]);
        } else if (a == "--cand-maxlen" && i + 1 < argc) {
            g_candMaxLen = stoi(argv[++i]);
        } else if (a == "--restart-kick" && i + 1 < argc) {
            restartKick = stoi(argv[++i]);
        } else if (a == "--abx-rate" && i + 1 < argc) {
            abxRate = stod(argv[++i]);
        } else if (a == "--polish-on-best") {
            polishOnBest = true;
        } else if (a == "--accept-eps" && i + 1 < argc) {
            acceptEps = stod(argv[++i]);
        } else if (a == "--cand-front" && i + 1 < argc) {
            candFront = stoi(argv[++i]);
        } else if (a == "--cand-dlb-strict") {
            dlbStrict = true;
        } else if (a == "--cand-2opt-both") {
            cand2optBoth = true;
        } else if (a == "--cand-no-rev") {
            g_candReversed = false;
        } else if (a == "--db-maxseg" && i + 1 < argc) {
            dbMaxSeg = stoi(argv[++i]);
        } else if (a == "--db-maxseg-div" && i + 1 < argc) {
            dbMaxSegDiv = stoi(argv[++i]);
        } else if (a == "--rvnd-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "single") rvndMode = RvndMode::Single;
            else if (m == "extended-oropt") rvndMode = RvndMode::ExtendedOrOpt;
            else if (m == "extended-oropt-wide") rvndMode = RvndMode::ExtendedOrOptWide;
            else if (m == "extended-oropt-rev") rvndMode = RvndMode::ExtendedOrOptRev;
            else if (m == "candidate") rvndMode = RvndMode::Candidate;
            else if (m == "candidate-dlb") rvndMode = RvndMode::CandidateDLB;
            else if (m == "lk-escape") rvndMode = RvndMode::LKEscape;
            else if (m == "adaptive-oropt") rvndMode = RvndMode::AdaptiveOrOpt;
            else { cerr << "Unknown --rvnd-mode: " << m << "\n"; return 1; }
        } else if (a == "--seed" && i + 1 < argc) {
            seed = stol(argv[++i]);
        } else if (a == "--adapt-kstart" && i + 1 < argc) {
            adaptKStart = stoi(argv[++i]);
        } else if (a == "--adapt-period" && i + 1 < argc) {
            adaptPeriod = stoi(argv[++i]);
        } else if (a == "--adapt-rho" && i + 1 < argc) {
            adaptRho = stod(argv[++i]);
        } else if (a == "--adapt-grow" && i + 1 < argc) {
            adaptGrow = stod(argv[++i]);
        } else if (a == "--adapt-shrink" && i + 1 < argc) {
            adaptShrink = stod(argv[++i]);
        } else if (a == "--max-time" && i + 1 < argc) {
            maxTimeSec = stod(argv[++i]);
        } else if (a == "-v") {
            verbose = true;
        }
    }

    /* Under a time limit, time is the binding constraint -- not I_max,
       unless the caller pinned it. */
    if (maxTimeSec > 0.0 && !imaxExplicit) I_max = 1000000000;

    if (poolSize < 1) poolSize = 1;

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    g_cand = make_candidate_list(eval, candK);
    set_cand_opts(candFront, cand2optBoth);
    set_dlb_strict(dlbStrict);

    if (dbMaxSegDiv > 0)
        dbMaxSeg = max(2, eval.Ncity / dbMaxSegDiv);

    vector<double> R;
    for (double r = 0.0; r <= 0.25; r += 0.01)
        R.push_back(r);

    Solution bestSol;
    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    /* One state for the whole run: the policy pools statistics across
       every RVND convergence to learn anything. */
    AdaptiveOrOptState adaptState;
    adaptState.kMax = max(AdaptiveOrOptState::K_FLOOR,
                          min(adaptKStart, (int)AdaptiveOrOptState::K_CAP));
    adaptState.kMaxMinSeen = adaptState.kMax;
    adaptState.kMaxMaxSeen = adaptState.kMax;
    for (int L = 2; L <= AdaptiveOrOptState::K_CAP; L++)
        adaptState.weight[L] = (L <= adaptState.kMax) ? 1.0 : 0.0;
    adaptState.period        = adaptPeriod;
    adaptState.rho           = adaptRho;
    adaptState.growHitRate   = adaptGrow;
    adaptState.shrinkHitRate = adaptShrink;

    gils_am_rvnd(bestSol, eval, I_max, I_ILS, R, poolSize, lambda, parentMode, rvndMode, gen,
                 adaptState, maxTimeSec, dbMaxSeg, dbFrontBias, acceptEps, polishOnBest,
                 abxRate, restartKick);

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "IILS " << I_ILS << "\n";
    cout << "RESTARTS " << g_restarts << "\n";
    if (abxRate > 0.0) cout << "CROSSOVERS " << g_crossovers << "\n";
    if (maxTimeSec > 0.0)
        cout << "MAX_TIME_S " << fixed << setprecision(3) << maxTimeSec << "\n";
    cout << "POOL " << poolSize << "\n";
    cout << "LAMBDA " << fixed << setprecision(2) << lambda << "\n";
    cout << "PARENT_MODE " << (parentMode == ParentMode::Pool ? "pool" : "pair") << "\n";
    cout << "DB_MAXSEG " << dbMaxSeg << "\n";
    if (rvndMode == RvndMode::Candidate || rvndMode == RvndMode::CandidateDLB)
        cout << "CAND_K " << g_cand.K << "  CAND_MAXLEN " << g_candMaxLen
             << "  CAND_REV " << (g_candReversed ? 1 : 0) << "\n";
    cout << "RVND_MODE " << (rvndMode == RvndMode::ExtendedOrOpt ? "extended-oropt"
                              : rvndMode == RvndMode::ExtendedOrOptWide ? "extended-oropt-wide"
                              : rvndMode == RvndMode::ExtendedOrOptRev ? "extended-oropt-rev"
                              : rvndMode == RvndMode::Candidate ? "candidate"
                              : rvndMode == RvndMode::CandidateDLB ? "candidate-dlb"
                              : rvndMode == RvndMode::LKEscape ? "lk-escape"
                              : rvndMode == RvndMode::AdaptiveOrOpt ? "adaptive-oropt" : "single") << "\n";
    if (rvndMode == RvndMode::AdaptiveOrOpt) {
        cout << "ADAPT_KMAX_FINAL " << adaptState.kMax << "\n";
        cout << "ADAPT_KMAX_RANGE " << adaptState.kMaxMinSeen << "-" << adaptState.kMaxMaxSeen << "\n";
        if (verbose) cerr << adaptState.summary();
    }
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
