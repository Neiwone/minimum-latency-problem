#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"
#include "rvnd_adaptive.h"
#include "neighborhoods_cand.h"

using namespace std;

/* Returns the position range the kick disturbed, so a don't-look-bit search
   can re-arm just that span ({-1,-1} = no-op). */
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

    // Segments: [0..p1-1], [p1..p2-1], [p2..p3-1], [p3..n-1]
    // Double-bridge: reconnect as seg1 + seg3 + seg2 + seg4
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

/* Applies `strength` kicks in sequence, returning the union of the ranges
   they disturbed. strength=1 is the original fixed-intensity perturbation. */
pair<int,int> perturb(Solution& sol, mt19937& gen, int strength) {
    int lo = INT_MAX, hi = -1;
    for (int k = 0; k < strength; k++) {
        auto r = double_bridge_once(sol, gen);
        if (r.first < 0) continue;
        lo = min(lo, r.first);
        hi = max(hi, r.second);
    }

    sol.calculateStructures();
    return hi < 0 ? make_pair(-1, -1) : make_pair(lo, hi);
}

/* Local search shared with gils_am_rvnd and mdm_gils_rvnd, so an equal-time
   comparison between the three is about strategy, not scan engineering. */
static CandList g_cand;
static int  g_candMaxLen  = 6;
static bool g_candReversed = true;

void print_trace(int outer, int step, const Solution& sol) {
    cout << "TRACE OUTER=" << outer << " STEP=" << step << " COST=" << sol.fEvaluationValue << " ROUTE=";
    for (int t = 0; t < sol.fN; t++)
        cout << sol.fTour[t] << (t + 1 < sol.fN ? "," : "");
    cout << "\n";
}

enum class PertMode { Fixed, Stagnation, Distance };

/* Nodes whose successor differs between two tours: an O(n) proxy for
   edge-set symmetric difference (Máximo & Nascimento's d(s, s_ref)). */
int edge_distance(const int* tourA, const int* tourB, int n) {
    vector<int> succA(n, -1), succB(n, -1);
    for (int i = 0; i + 1 < n; i++) succA[tourA[i]] = tourA[i + 1];
    for (int i = 0; i + 1 < n; i++) succB[tourB[i]] = tourB[i + 1];

    int diff = 0;
    for (int u = 0; u < n; u++)
        if (succA[u] != succB[u]) diff++;
    return diff;
}

/* H1 "stagnation": strength grows every `stagnationStep` non-improving
   iterations. Rejected -- escalates blindly, without checking diversity. */
int stagnation_strength(int iterILS, int stagnationStep, int maxStrength) {
    int strength = 1 + iterILS / stagnationStep;
    return min(strength, maxStrength);
}

/* H2: pool of the best distinct restart solutions, sorted by cost. Only
   the tour is kept; idle members are never RVND'd directly. */
struct EliteEntry { Cost cost; vector<int> tour; };

void add_elite(vector<EliteEntry>& elite, const Solution& sol, int maxSize) {
    for (const auto& e : elite)
        if (e.cost == sol.fEvaluationValue &&
            equal(e.tour.begin(), e.tour.end(), sol.fTour))
            return;

    elite.push_back({sol.fEvaluationValue, vector<int>(sol.fTour, sol.fTour + sol.fN)});
    sort(elite.begin(), elite.end(), [](const EliteEntry& a, const EliteEntry& b) {
        return a.cost < b.cost;
    });
    if ((int)elite.size() > maxSize) elite.pop_back();
}

/* Path relinking (Glover): walk `start` towards `guide` one swap at a time,
   returning the best tour on the path. O(n^3), so once per restart only. */
Solution path_relink(const Solution& start, const vector<int>& guideTour) {
    Solution current(start);
    int n = current.fN;

    vector<int> pos(n);
    for (int i = 0; i < n; i++) pos[current.fTour[i]] = i;

    Solution best(current);

    for (int i = 1; i < n; i++) {
        if (current.fTour[i] == guideTour[i]) continue;

        int v = guideTour[i];
        int j = pos[v];
        int u = current.fTour[i];

        swap(current.fTour[i], current.fTour[j]);
        pos[u] = j;
        pos[v] = i;
        current.calculateStructures();

        if (current.fEvaluationValue < best.fEvaluationValue)
            best = current;
    }
    return best;
}

/* H4: Single is the original first-improvement RVND; Multi batches
   non-conflicting moves per scan. Single is the default. */
enum class RvndMode { Single, Multi, ExtendedOrOpt, ExtendedOrOptWide, ExtendedOrOpt3Opt,
                      AdaptiveOrOpt, ExtendedOrOptRev, Candidate, CandidateDLB };

/* `adaptState` carries the adaptive-or-opt learning across every RVND
   call of the run (see include/rvnd_adaptive.h); ignored by other modes. */
void run_rvnd(RvndMode mode, Solution& sol, mt19937& gen, AdaptiveOrOptState& adaptState,
              DlbState& dlb) {
    if (mode == RvndMode::CandidateDLB) RVND_CandidateDLB(sol, g_cand, g_candMaxLen, g_candReversed, gen, dlb);
    else if (mode == RvndMode::Candidate) RVND_Candidate(sol, g_cand, g_candMaxLen, g_candReversed, gen);
    else if (mode == RvndMode::ExtendedOrOptRev) RVND_ExtendedOrOptRev(sol, gen);
    else if (mode == RvndMode::Multi) RVND_Multi(sol, gen);
    else if (mode == RvndMode::ExtendedOrOpt) RVND_ExtendedOrOpt(sol, gen);
    else if (mode == RvndMode::ExtendedOrOptWide) RVND_ExtendedOrOptWide(sol, gen);
    else if (mode == RvndMode::ExtendedOrOpt3Opt) RVND_ExtendedOrOpt3Opt(sol, gen);
    else if (mode == RvndMode::AdaptiveOrOpt) RVND_AdaptiveOrOpt(sol, gen, adaptState);
    else RVND(sol, gen);
}

/* H6: Greedy is the original construction(); Lookahead scores candidates
   by a k-step greedy rollout instead of dist(r,c). */
enum class ConstructionMode { Greedy, Lookahead };

/* Completed restarts, reported so a fixed-time protocol can verify
   that mechanisms living at restart boundaries were exercised at all. */
long g_restarts = 0;
long g_ilsIters = 0;   /* perturbations applied: a speed measure for the ablation */

void gils_rvnd(Solution& bestSol, Evaluator& eval,
               int I_max, int I_ILS, const vector<double>& R, bool verbose,
               PertMode pertMode, int stagnationStep, int maxStrength,
               double targetMinFrac, double targetMaxFrac,
               bool pathRelinking, int eliteSize, RvndMode rvndMode,
               ConstructionMode constructionMode, int lookaheadK, mt19937& gen,
               AdaptiveOrOptState& adaptState, double maxTimeSec) {
    Cost fStar = LLONG_MAX;
    vector<EliteEntry> elite;
    DlbState dlb;

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

        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        Solution s;
        if (constructionMode == ConstructionMode::Lookahead)
            construction_lookahead(s, eval, alpha, lookaheadK, gen);
        else
            construction(s, eval, alpha, gen);

        /* A fresh construction is nowhere near a local optimum: arm
           everything. Only perturbations get the cheap partial re-arm. */
        dlb.reset(s.fN);

        Solution sPrime(s);

        int n = s.fN;
        int targetMin = max(1, (int)round(targetMinFrac * n));
        int targetMax = max(targetMin + 1, (int)round(targetMaxFrac * n));

        int iterILS = 0;
        int step = 0;
        int strength = 1;
        /* Tour the last perturbation started from -- "distance" mode
           measures against it how much diversity that cycle achieved. */
        vector<int> referenceTour(sPrime.fTour, sPrime.fTour + n);

        while (iterILS < I_ILS) {
            run_rvnd(rvndMode, s, gen, adaptState, dlb);

            if (pertMode == PertMode::Distance) {
                int d = edge_distance(s.fTour, referenceTour.data(), n);
                if (d < targetMin) strength = min(strength + 1, maxStrength);
                else if (d > targetMax) strength = max(strength - 1, 1);
            }

            if (s.fEvaluationValue < sPrime.fEvaluationValue) {
                sPrime = s;
                iterILS = 0;
                if (verbose) print_trace(i, step, sPrime);
            }

            if (outOfTime()) break;

            s = sPrime;
            referenceTour.assign(sPrime.fTour, sPrime.fTour + n);

            int thisStrength = 1;
            if (pertMode == PertMode::Stagnation)
                thisStrength = stagnation_strength(iterILS, stagnationStep, maxStrength);
            else if (pertMode == PertMode::Distance)
                thisStrength = strength;

            auto hit = perturb(s, gen, thisStrength);
            if (hit.first >= 0) dlb.arm_range(s, hit.first - 1, hit.second + 1);
            else dlb.reset(s.fN);

            iterILS++;
            g_ilsIters++;
            step++;
        }

        if (pathRelinking && !elite.empty()) {
            uniform_int_distribution<int> eliteDist(0, (int)elite.size() - 1);
            const vector<int>& guide = elite[eliteDist(gen)].tour;

            Solution prResult = path_relink(sPrime, guide);
            dlb.reset(prResult.fN);
            run_rvnd(rvndMode, prResult, gen, adaptState, dlb);

            if (prResult.fEvaluationValue < sPrime.fEvaluationValue) {
                sPrime = prResult;
                if (verbose) print_trace(i, step, sPrime);
            }
        }

        if (pathRelinking) add_elite(elite, sPrime, eliteSize);

        if (sPrime.fEvaluationValue < fStar) {
            bestSol = sPrime;
            fStar = sPrime.fEvaluationValue;
        }
    }
}


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./gils_rvnd <instance.tsp> [--imax 10] [--iils 50]\n";
        cerr << "    [--pert-mode fixed|stagnation|distance] [--stagnation-step 5]\n";
        cerr << "    [--max-strength 5] [--target-min-pct 0.05] [--target-max-pct 0.15]\n";
        cerr << "    [--path-relinking] [--elite-size 5]\n";
        cerr << "    [--rvnd-mode single|multi|extended-oropt|extended-oropt-wide|extended-oropt-3opt|\n";
        cerr << "                 extended-oropt-rev|candidate|candidate-dlb|adaptive-oropt]\n";
        cerr << "    [--cand-k 12] [--cand-maxlen 6] [--cand-no-rev] [--cand-drop swap,2opt,oropt1..6,rev2..6]\n";
        cerr << "    [--max-time SECONDS]\n";
        cerr << "    [--construction-mode greedy|lookahead] [--lookahead-k 3]\n";
        cerr << "    [--seed N] [-v]\n";
        cerr << "    [--closed]  pay the return to the depot (default: open path)\n";
        cerr << "    [--nint|--trunc]  EUC_2D: force TSPLIB nint / truncation (default: truncation\n";
        cerr << "                on the path, nint with --closed, as in the literature)\n";
        return 1;
    }

    string instanceFile = argv[1];
    int I_max = 10;
    int I_ILS = 100;
    int candK = 12;
    string candDrop;    /* neighborhoods left out, for the ablation */
    bool verbose = false;
    PertMode pertMode = PertMode::Fixed;
    int stagnationStep = 5;
    int maxStrength = 5;
    double targetMinFrac = 0.05;
    double targetMaxFrac = 0.15;
    bool pathRelinking = false;
    int eliteSize = 5;
    RvndMode rvndMode = RvndMode::Single;
    ConstructionMode constructionMode = ConstructionMode::Greedy;
    int lookaheadK = 3;
    long seed = -1;
    double maxTimeSec = -1.0;   /* <=0 disables the time limit */
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
        }
        else if (a == "--iils" && i + 1 < argc) {
            I_ILS = stoi(argv[++i]);
        }
        else if (a == "--pert-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "fixed") pertMode = PertMode::Fixed;
            else if (m == "stagnation") pertMode = PertMode::Stagnation;
            else if (m == "distance") pertMode = PertMode::Distance;
            else { cerr << "Unknown --pert-mode: " << m << "\n"; return 1; }
        }
        else if (a == "--stagnation-step" && i + 1 < argc) {
            stagnationStep = stoi(argv[++i]);
        }
        else if (a == "--max-strength" && i + 1 < argc) {
            maxStrength = stoi(argv[++i]);
        }
        else if (a == "--target-min-pct" && i + 1 < argc) {
            targetMinFrac = stod(argv[++i]);
        }
        else if (a == "--target-max-pct" && i + 1 < argc) {
            targetMaxFrac = stod(argv[++i]);
        }
        else if (a == "--path-relinking") {
            pathRelinking = true;
        }
        else if (a == "--elite-size" && i + 1 < argc) {
            eliteSize = stoi(argv[++i]);
        }
        else if (a == "--rvnd-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "single") rvndMode = RvndMode::Single;
            else if (m == "multi") rvndMode = RvndMode::Multi;
            else if (m == "extended-oropt") rvndMode = RvndMode::ExtendedOrOpt;
            else if (m == "extended-oropt-wide") rvndMode = RvndMode::ExtendedOrOptWide;
            else if (m == "extended-oropt-3opt") rvndMode = RvndMode::ExtendedOrOpt3Opt;
            else if (m == "adaptive-oropt") rvndMode = RvndMode::AdaptiveOrOpt;
            else if (m == "extended-oropt-rev") rvndMode = RvndMode::ExtendedOrOptRev;
            else if (m == "candidate") rvndMode = RvndMode::Candidate;
            else if (m == "candidate-dlb") rvndMode = RvndMode::CandidateDLB;
            else { cerr << "Unknown --rvnd-mode: " << m << "\n"; return 1; }
        }
        else if (a == "--cand-k" && i + 1 < argc) candK = stoi(argv[++i]);
        else if (a == "--cand-maxlen" && i + 1 < argc) g_candMaxLen = stoi(argv[++i]);
        else if (a == "--cand-no-rev") g_candReversed = false;
        else if (a == "--cand-drop" && i + 1 < argc) candDrop = argv[++i];
        else if (a == "--construction-mode" && i + 1 < argc) {
            string m = argv[++i];
            if (m == "greedy") constructionMode = ConstructionMode::Greedy;
            else if (m == "lookahead") constructionMode = ConstructionMode::Lookahead;
            else { cerr << "Unknown --construction-mode: " << m << "\n"; return 1; }
        }
        else if (a == "--lookahead-k" && i + 1 < argc) {
            lookaheadK = stoi(argv[++i]);
        }
        else if (a == "--closed") {
            set_closed_tour(true);
        }
        else if (a == "--nint") {
            set_euc_round(EucRound::Nint);
        }
        else if (a == "--trunc") {
            set_euc_round(EucRound::Trunc);
        }
        else if (a == "--seed" && i + 1 < argc) {
            seed = stol(argv[++i]);
        }
        else if (a == "--max-time" && i + 1 < argc) {
            maxTimeSec = stod(argv[++i]);
        }
        else if (a == "--adapt-kstart" && i + 1 < argc) { adaptKStart = stoi(argv[++i]); }
        else if (a == "--adapt-period" && i + 1 < argc) { adaptPeriod = stoi(argv[++i]); }
        else if (a == "--adapt-rho" && i + 1 < argc) { adaptRho = stod(argv[++i]); }
        else if (a == "--adapt-grow" && i + 1 < argc) { adaptGrow = stod(argv[++i]); }
        else if (a == "--adapt-shrink" && i + 1 < argc) { adaptShrink = stod(argv[++i]); }
        else if (a == "-v") {
            verbose = true;
        }
    }

    /* Under a time limit, time is meant to be the binding constraint, so
       the restart count stops being one unless the caller pinned it. */
    if (maxTimeSec > 0.0 && !imaxExplicit) I_max = 1000000000;

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos) {
        filepath = "instances/" + instanceFile;
    }

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    g_cand = make_candidate_list(eval, candK);
    if (!set_cand_disabled(candDrop, g_candMaxLen)) {
        cerr << "Unknown neighborhood in --cand-drop: " << candDrop << "\n";
        return 1;
    }

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

    gils_rvnd(bestSol, eval, I_max, I_ILS, R, verbose, pertMode, stagnationStep, maxStrength,
              targetMinFrac, targetMaxFrac, pathRelinking, eliteSize, rvndMode,
              constructionMode, lookaheadK, gen, adaptState, maxTimeSec);

    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    const char* pertModeName = pertMode == PertMode::Fixed ? "fixed"
                              : pertMode == PertMode::Stagnation ? "stagnation" : "distance";

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "IILS " << I_ILS << "\n";
    cout << "RESTARTS " << g_restarts << "\n";
    cout << "ILS_ITERS " << g_ilsIters << "\n";
    if (maxTimeSec > 0.0)
        cout << "MAX_TIME_S " << fixed << setprecision(3) << maxTimeSec << "\n";
    cout << "PERT_MODE " << pertModeName << "\n";
    cout << "PATH_RELINKING " << (pathRelinking ? "on" : "off") << "\n";
    cout << "CLOSED " << (closed_tour() ? 1 : 0) << "\n";
    cout << "NINT " << (euc_nint() ? 1 : 0) << "\n";
    cout << "RVND_MODE " << (rvndMode == RvndMode::Multi ? "multi"
                              : rvndMode == RvndMode::ExtendedOrOpt ? "extended-oropt"
                              : rvndMode == RvndMode::ExtendedOrOptWide ? "extended-oropt-wide"
                              : rvndMode == RvndMode::ExtendedOrOpt3Opt ? "extended-oropt-3opt"
                              : rvndMode == RvndMode::AdaptiveOrOpt ? "adaptive-oropt"
                              : rvndMode == RvndMode::ExtendedOrOptRev ? "extended-oropt-rev"
                              : rvndMode == RvndMode::Candidate ? "candidate"
                              : rvndMode == RvndMode::CandidateDLB ? "candidate-dlb" : "single") << "\n";
    if (rvndMode == RvndMode::Candidate || rvndMode == RvndMode::CandidateDLB) {
        cout << "CAND_K " << g_cand.K << "  CAND_MAXLEN " << g_candMaxLen << "\n";
        if (!candDrop.empty()) cout << "CAND_DROP " << candDrop << "\n";
    }
    if (rvndMode == RvndMode::AdaptiveOrOpt) {
        cout << "ADAPT_KMAX_FINAL " << adaptState.kMax << "\n";
        cout << "ADAPT_KMAX_RANGE " << adaptState.kMaxMinSeen << "-" << adaptState.kMaxMaxSeen << "\n";
        if (verbose) cerr << adaptState.summary();
    }
    cout << "CONSTRUCTION_MODE " << (constructionMode == ConstructionMode::Lookahead ? "lookahead" : "greedy") << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++) {
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];
    }

    return 0;
}
