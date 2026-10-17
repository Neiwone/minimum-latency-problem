#include <bits/stdc++.h>
#include <cstdio>
#include <unistd.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"
#include "neighborhoods_cand.h"
#include "fpmax_mining.h"

using namespace std;

/* H13: MDM-GILS-RVND (Santana, Plastino & Rosseti, arXiv:1908.10705). */

/* Mines maximal frequent ARC SEGMENTS from the elite pool with FPMax*, then
   splices whole sub-paths into new constructions as atomic units. */

/* Two-phase: the first half of the budget fills the elite pool, the second
   re-mines it every time it changes. */

/* Returns the position range the perturbation disturbed, so the don't-look
   bit search can re-arm just that span ({-1,-1} = no-op). */
pair<int,int> double_bridge_once(Solution& sol, mt19937& gen) {
    int n = sol.fN;
    if (n < 8) return {-1, -1};

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

    return {p1, p3 - 1};
}

pair<int,int> perturb(Solution& sol, mt19937& gen) {
    auto range = double_bridge_once(sol, gen);
    sol.calculateStructures();
    return range;
}

/* Local search shared with gils_am_rvnd, so an equal-time comparison between
   the two is about search strategy and not about scan engineering. */
enum class RvndMode { Single, CandidateDLB };
static RvndMode g_rvndMode = RvndMode::Single;
static CandList g_cand;
static int  g_candMaxLen  = 6;
static bool g_candReversed = true;

void run_rvnd(Solution& sol, mt19937& gen, DlbState& dlb) {
    if (g_rvndMode == RvndMode::CandidateDLB)
        RVND_CandidateDLB(sol, g_cand, g_candMaxLen, g_candReversed, gen, dlb);
    else
        RVND(sol, gen);
}

struct EliteSet {
    vector<Solution> sols;
    int maxSize;
    bool dirty = false; // true if changed since last mining

    explicit EliteSet(int maxSize_) : maxSize(maxSize_) {}

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
        dirty = true;
    }
};

struct Segment {
    vector<int> nodes; // consecutive customers, length >= 2
};

/* FPMax* must stay IN-MEMORY: shelling out to Python per call once blew a
   15s fixed-time budget out to 69.6s of wall clock on att532. */
vector<Segment> mine_patterns(const EliteSet& elite, double supMin, int maxPatterns) {
    if (elite.sols.empty()) return {};

    int n = elite.sols.front().fN;

    vector<vector<int>> tours;
    tours.reserve(elite.sols.size());
    for (const auto& s : elite.sols)
        tours.emplace_back(s.fTour, s.fTour + s.fN);

    vector<Segment> candidates;
    for (auto& path : fpmax_mine_arc_paths(tours, n, supMin, maxPatterns))
        candidates.push_back({std::move(path)});

    return candidates;
}

/* Algorithm 5: construction() plus, when the chosen candidate opens a
   still-unvisited mined segment, splicing that whole segment in at once. */
void construction_mdm(Solution& sol, Evaluator& eval, double alpha,
                       const unordered_map<int, Segment>& segStarts, mt19937& gen) {
    int n = eval.Ncity;
    double alphaClamped = max(0.0, min(alpha, 1.0));

    vector<bool> visited(n, false);
    vector<int> route;
    route.reserve(n);
    route.push_back(0);
    visited[0] = true;
    int current = 0;

    auto segmentViable = [&](const Segment& seg) {
        for (int node : seg.nodes) if (visited[node]) return false;
        return true;
    };

    while ((int)route.size() < n) {
        vector<int> candidates;
        for (int v = 1; v < n; v++)
            if (!visited[v]) candidates.push_back(v);

        vector<pair<int, int>> scored; // (node, distance)
        scored.reserve(candidates.size());
        int minCost = INT_MAX, maxCost = INT_MIN;
        for (int v : candidates) {
            int d = eval.fEdgeDis[current][v];
            scored.push_back({v, d});
            minCost = min(minCost, d);
            maxCost = max(maxCost, d);
        }

        int threshold = minCost + (int)llround(alphaClamped * (maxCost - minCost));
        vector<int> rcl;
        for (const auto& [v, d] : scored)
            if (d <= threshold) rcl.push_back(v);
        if (rcl.empty()) rcl.push_back(scored.front().first);

        uniform_int_distribution<int> dist(0, (int)rcl.size() - 1);
        int chosen = rcl[dist(gen)];

        auto it = segStarts.find(chosen);
        if (it != segStarts.end() && segmentViable(it->second)) {
            for (int node : it->second.nodes) { route.push_back(node); visited[node] = true; }
            current = it->second.nodes.back();
        } else {
            route.push_back(chosen);
            visited[chosen] = true;
            current = chosen;
        }
    }

    sol.Define(n);
    sol.fDist = eval.fEdgeDis;
    for (int i = 0; i < n; i++) sol.fTour[i] = route[i];
    sol.calculateStructures();
}

/* Reported by main() so "did mining actually fire?" is verifiable instead
   of assumed -- an --imax 1 bug once hid behind exactly that. */
long g_miningCalls = 0;
long g_patternRestarts = 0;
long g_restarts = 0;

void mdm_gils_rvnd(Solution& bestSol, Evaluator& eval, int I_max, int I_ILS,
                    const vector<double>& R, int poolSize, double supMin,
                    int maxPatterns, mt19937& gen, double maxTimeSec) {
    Cost fStar = LLONG_MAX;
    EliteSet elite(poolSize);
    DlbState dlb;
    unordered_map<int, Segment> segStarts; // empty until phase 2 mines something

    int phase1Iters = max(1, I_max / 2);

    /* Wall-clock stop. The phase split must then follow TIME, not restart
       count, or mining silently never fires in short runs. */
    using SteadyClock = chrono::steady_clock;
    const auto tStart = SteadyClock::now();
    const bool timed = maxTimeSec > 0.0;
    auto elapsedSec = [&]() {
        return chrono::duration<double>(SteadyClock::now() - tStart).count();
    };
    auto outOfTime = [&]() { return timed && elapsedSec() >= maxTimeSec; };
    auto inMiningPhase = [&](int i) {
        return timed ? (elapsedSec() >= 0.5 * maxTimeSec) : (i >= phase1Iters);
    };

    for (int i = 0; i < I_max; i++) {
        if (outOfTime()) break;

        g_restarts++;
        bool usePatterns = inMiningPhase(i) && !segStarts.empty();

        if (inMiningPhase(i) && elite.dirty) {
            vector<Segment> segs = mine_patterns(elite, supMin, maxPatterns);
            g_miningCalls++;
            segStarts.clear();
            for (auto& seg : segs) segStarts[seg.nodes.front()] = seg;
            elite.dirty = false;
            usePatterns = !segStarts.empty();
        }

        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        Solution s;
        if (usePatterns) { construction_mdm(s, eval, alpha, segStarts, gen); g_patternRestarts++; }
        else construction(s, eval, alpha, gen);

        /* A fresh construction is nowhere near a local optimum: arm
           everything. Only perturbations get the cheap partial re-arm. */
        dlb.reset(s.fN);

        Solution sPrime(s);

        int iterILS = 0;
        while (iterILS < I_ILS) {
            run_rvnd(s, gen, dlb);

            /* Algorithm 4 updates the elite set HERE, on every RVND result
               -- not once per restart, or short runs never mine. */
            elite.add(s);

            if (s.fEvaluationValue < sPrime.fEvaluationValue) {
                sPrime = s;
                iterILS = 0;
            }

            if (outOfTime()) break;

            s = sPrime;
            auto hit = perturb(s, gen);
            if (hit.first >= 0) dlb.arm_range(s, hit.first - 1, hit.second + 1);
            else dlb.reset(s.fN);
            iterILS++;
        }

        elite.add(sPrime);

        if (sPrime.fEvaluationValue < fStar) {
            bestSol = sPrime;
            fStar = sPrime.fEvaluationValue;
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./mdm_gils_rvnd <instance.tsp> [--imax 10] [--iils 100] [--pool 10]\n";
        cerr << "    [--sup-min 0.70] [--max-patterns 5] [--max-time SECONDS] [--seed N]\n";
        cerr << "    [--closed]  pay the return to the depot (default: open path)\n";
        cerr << "    [--nint]    round EUC_2D distances to nearest (TSPLIB) instead of truncating\n";
        cerr << "    [--rvnd-mode single|candidate-dlb] [--cand-k 12] [--cand-maxlen 6] [--cand-no-rev]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int I_max = 10;
    int I_ILS = 100;
    int poolSize = 10;
    double supMin = 0.70;
    int maxPatterns = 5;
    double maxTimeSec = -1.0;   /* <=0 disables the time limit */
    bool imaxExplicit = false;
    long seed = -1;
    int candK = 12;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--imax" && i + 1 < argc) { I_max = stoi(argv[++i]); imaxExplicit = true; }
        else if (a == "--iils" && i + 1 < argc) I_ILS = stoi(argv[++i]);
        else if (a == "--pool" && i + 1 < argc) poolSize = stoi(argv[++i]);
        else if (a == "--sup-min" && i + 1 < argc) supMin = stod(argv[++i]);
        else if (a == "--max-patterns" && i + 1 < argc) maxPatterns = stoi(argv[++i]);
        else if (a == "--max-time" && i + 1 < argc) maxTimeSec = stod(argv[++i]);
        else if (a == "--closed") set_closed_tour(true);
        else if (a == "--nint") set_euc_nint(true);
        else if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
        else if (a == "--cand-k" && i + 1 < argc) candK = stoi(argv[++i]);
        else if (a == "--cand-maxlen" && i + 1 < argc) g_candMaxLen = stoi(argv[++i]);
        else if (a == "--cand-no-rev") g_candReversed = false;
        else if (a == "--rvnd-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "single") g_rvndMode = RvndMode::Single;
            else if (m == "candidate-dlb") g_rvndMode = RvndMode::CandidateDLB;
            else { cerr << "Unknown --rvnd-mode: " << m << "\n"; return 1; }
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

    vector<double> R;
    for (double r = 0.0; r <= 0.25; r += 0.01) R.push_back(r);

    Solution bestSol;
    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    mdm_gils_rvnd(bestSol, eval, I_max, I_ILS, R, poolSize, supMin, maxPatterns, gen, maxTimeSec);

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "CLOSED " << (closed_tour() ? 1 : 0) << "\n";
    cout << "NINT " << (euc_nint() ? 1 : 0) << "\n";
    cout << "RVND_MODE " << (g_rvndMode == RvndMode::CandidateDLB ? "candidate-dlb" : "single") << "\n";
    if (g_rvndMode == RvndMode::CandidateDLB)
        cout << "CAND_K " << g_cand.K << "  CAND_MAXLEN " << g_candMaxLen << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "IILS " << I_ILS << "\n";
    cout << "POOL " << poolSize << "\n";
    cout << "SUP_MIN " << fixed << setprecision(2) << supMin << "\n";
    cout << "MAX_PATTERNS " << maxPatterns << "\n";
    cout << "RESTARTS " << g_restarts << "\n";
    cout << "MINING_CALLS " << g_miningCalls << "\n";
    cout << "PATTERN_RESTARTS " << g_patternRestarts << "\n";
    if (maxTimeSec > 0.0)
        cout << "MAX_TIME_S " << fixed << setprecision(3) << maxTimeSec << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
