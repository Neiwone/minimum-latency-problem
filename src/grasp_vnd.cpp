#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"

using namespace std;

/* H_Salehipour: GRASP+VND and GRASP+VNS for the TRP (Salehipour, Sorensen,
   Goos & Braysy, "Efficient GRASP+VND and GRASP+VNS metaheuristics for
   the traveling repairman problem", 4OR 9:189-209, 2011). See
   docs/experiments/h-salehipour-grasp-vnd.md.

   Distinct from the Silva et al. (2012) GILS-RVND this project is based
   on: fixed-COUNT RCL (alpha closest candidates, not alpha% of the
   greedy range), and 5 DIFFERENT neighborhoods (swap, swap-adjacent,
   2-opt, or-opt [lengths 1-3, single neighborhood], remove-insert [per
   vertex, relocate the vertex farthest from it to the end of the tour]
   -- this last one is unique to this paper, not present in GILS-RVND).

   Implements "setting 1" from the paper (NoFix, Full proximity -- no
   neighborhood-size reduction): the most literal, unreduced
   reproduction of Algorithms 1-4. The Fix/Half neighborhood-reduction
   schemes (Sect. 2.3.2) are documented as not implemented (pure 2011-
   hardware speed optimizations, not required for a faithful quality
   comparison on modern hardware).

   Reuses this project's Solution class (T/C/Cr tables, same O(1) move
   evaluation trick -- the objective f(x) = sum (n-i+1)*w(x_{i-1},x_i) is
   identical to GILS-RVND's cumulative latency). Move delta functions
   below mirror Solution::evaluate{Swap,2Opt,Reinsertion,OrOpt}'s exact
   internal logic (see src/solution.cpp) but return the signed delta
   instead of a boolean, since VND/VNS here need the single BEST move in
   a neighborhood (arg min), not just the first improving one. */

int delta_swap(const Solution& s, int i, int j) {
    if (i > j) swap(i, j);
    int t = 0, c = 0; bool first = true; int last = -1;
    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = s.getT(u, v), Cu = s.getC(u, v), Wu = s.getW(u, v);
        int firstNode = s.fTour[u], lastNode = s.fTour[v];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = s.fDist[last][firstNode];
        c += Wu * (t + e) + Cu; t += e + Tu; last = lastNode;
    };
    append(0, i - 1); append(j, j); append(i + 1, j - 1); append(i, i); append(j + 1, s.fN - 1);
    return c - s.fEvaluationValue;
}

int delta_2opt(const Solution& s, int i, int j) {
    if (i > j) swap(i, j);
    int t = 0, c = 0; bool first = true; int last = -1;
    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = s.getT(u, v), Cu = s.getC(u, v), Wu = s.getW(u, v);
        int firstNode = s.fTour[u], lastNode = s.fTour[v];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = s.fDist[last][firstNode];
        c += Wu * (t + e) + Cu; t += e + Tu; last = lastNode;
    };
    auto appendReversed = [&](int u, int v) {
        if (u > v) return;
        int Tu = s.getT(u, v), Cu = s.getCr(u, v), Wu = s.getW(u, v);
        int firstNode = s.fTour[v], lastNode = s.fTour[u];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = s.fDist[last][firstNode];
        c += Wu * (t + e) + Cu; t += e + Tu; last = lastNode;
    };
    append(0, i - 1); appendReversed(i, j); append(j + 1, s.fN - 1);
    return c - s.fEvaluationValue;
}

int delta_reinsertion(const Solution& s, int i, int j) {
    if (i == j) return 0;
    int t = 0, c = 0; bool first = true; int last = -1;
    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = s.getT(u, v), Cu = s.getC(u, v), Wu = s.getW(u, v);
        int firstNode = s.fTour[u], lastNode = s.fTour[v];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = s.fDist[last][firstNode];
        c += Wu * (t + e) + Cu; t += e + Tu; last = lastNode;
    };
    if (i < j) { append(0, i - 1); append(i + 1, j); append(i, i); append(j + 1, s.fN - 1); }
    else       { append(0, j); append(i, i); append(j + 1, i - 1); append(i + 1, s.fN - 1); }
    return c - s.fEvaluationValue;
}

int delta_oropt(const Solution& s, int i, int j, int k) {
    if (k >= i && k <= j) return INT_MAX;
    int t = 0, c = 0; bool first = true; int last = -1;
    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = s.getT(u, v), Cu = s.getC(u, v), Wu = s.getW(u, v);
        int firstNode = s.fTour[u], lastNode = s.fTour[v];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        int e = s.fDist[last][firstNode];
        c += Wu * (t + e) + Cu; t += e + Tu; last = lastNode;
    };
    if (k < i) { append(0, k); append(i, j); append(k + 1, i - 1); append(j + 1, s.fN - 1); }
    else       { append(0, i - 1); append(j + 1, k); append(i, j); append(k + 1, s.fN - 1); }
    return c - s.fEvaluationValue;
}

/* apply reinsertion: move the element at position i to right after
   position j (both interpretations of Reinsertion and of Or-opt's
   segment relocation collapse to the same index arithmetic). */
void apply_reinsertion(vector<int>& tour, int i, int j) {
    int val = tour[i];
    tour.erase(tour.begin() + i);
    int insertPos = (i < j) ? j : j + 1;
    tour.insert(tour.begin() + insertPos, val);
}

void apply_oropt(vector<int>& tour, int i, int j, int k) {
    int segLen = j - i + 1;
    vector<int> seg(tour.begin() + i, tour.begin() + j + 1);
    tour.erase(tour.begin() + i, tour.begin() + j + 1);
    int insertPos = (k < i) ? k + 1 : k - segLen + 1;
    tour.insert(tour.begin() + insertPos, seg.begin(), seg.end());
}

/* Precomputed once: farthest[v] = vertex geometrically farthest from v
   (static property of the distance matrix, independent of tour order --
   see Sect 2.3.1, "remove-insert" neighborhood). */
vector<int> compute_farthest(int n, int** dist) {
    vector<int> farthest(n);
    for (int i = 0; i < n; i++) {
        int best = -1, bestD = -1;
        // j starts at 1: vertex 0 is the depot, fixed at tour position 0 by
        // construction and by every neighborhood here (all scans start
        // their moved range at position >=1) -- it must never be a
        // relocation target for remove-insert either, or that invariant
        // breaks.
        for (int j = 1; j < n; j++) {
            if (j == i) continue;
            if (dist[i][j] > bestD) { bestD = dist[i][j]; best = j; }
        }
        farthest[i] = best;
    }
    return farthest;
}

enum Neighborhood { SWAP_ADJACENT, REMOVE_INSERT, SWAP, TWO_OPT, OR_OPT, N_NEIGHBORHOODS };

/* Refreshes T/C/Cr from the current tour, then scans neighborhood `nb`
   in full (best-improvement: finds the single best move, arg min Nk),
   applies it if it improves, and reports whether it did -- Algorithm 3's
   "local search: x' <- arg min Nk(x)" step. */
bool best_move_in_neighborhood(int nb, vector<int>& tour, Solution& sol,
                                const vector<int>& farthest, int orOptMaxLen) {
    int n = sol.fN;
    for (int i = 0; i < n; i++) sol.fTour[i] = tour[i];
    sol.calculateStructures();

    int bestDelta = 0; // must be < 0 to accept -- track strictly best found
    int bi = -1, bj = -1, bk = -1;

    switch (nb) {
        case SWAP_ADJACENT: {
            for (int i = 1; i < n - 1; i++) {
                int d = delta_swap(sol, i, i + 1);
                if (d < bestDelta) { bestDelta = d; bi = i; bj = i + 1; }
            }
            break;
        }
        case SWAP: {
            for (int i = 1; i < n; i++)
                for (int j = i + 1; j < n; j++) {
                    int d = delta_swap(sol, i, j);
                    if (d < bestDelta) { bestDelta = d; bi = i; bj = j; }
                }
            break;
        }
        case TWO_OPT: {
            for (int i = 1; i < n; i++)
                for (int j = i + 1; j < n; j++) {
                    int d = delta_2opt(sol, i, j);
                    if (d < bestDelta) { bestDelta = d; bi = i; bj = j; }
                }
            break;
        }
        case OR_OPT: {
            for (int segLen = 1; segLen <= orOptMaxLen; segLen++) {
                for (int i = 1; i + segLen - 1 < n; i++) {
                    int j = i + segLen - 1;
                    for (int k = 0; k < n; k++) {
                        if (k >= i && k <= j) continue;
                        int d = delta_oropt(sol, i, j, k);
                        if (d < bestDelta) { bestDelta = d; bi = i; bj = j; bk = k; }
                    }
                }
            }
            break;
        }
        case REMOVE_INSERT: {
            vector<int> posOf(n);
            for (int p = 0; p < n; p++) posOf[tour[p]] = p;
            for (int i = 1; i < n; i++) {
                int v = tour[i];
                int f = farthest[v];
                int fp = posOf[f];
                if (fp == n - 1) continue; // already at the end
                int d = delta_reinsertion(sol, fp, n - 1);
                if (d < bestDelta) { bestDelta = d; bi = fp; bj = n - 1; }
            }
            break;
        }
    }

    if (bestDelta >= 0) return false;

    switch (nb) {
        case SWAP_ADJACENT:
        case SWAP:
            swap(tour[bi], tour[bj]);
            break;
        case TWO_OPT:
            reverse(tour.begin() + bi, tour.begin() + bj + 1);
            break;
        case OR_OPT:
            apply_oropt(tour, bi, bj, bk);
            break;
        case REMOVE_INSERT:
            apply_reinsertion(tour, bi, bj);
            break;
    }
    return true;
}

int tour_cost(const vector<int>& tour, int** dist) {
    int t = 0, total = 0;
    for (size_t i = 1; i < tour.size(); i++) {
        t += dist[tour[i - 1]][tour[i]];
        total += t;
    }
    return total;
}

/* Algorithm 2: fixed-count RCL by proximity (alpha closest candidates,
   NOT alpha% of the greedy range as in GILS-RVND's construction). */
vector<int> construction_salehipour(Evaluator& eval, int alpha, mt19937& gen) {
    int n = eval.Ncity;
    vector<bool> visited(n, false);
    vector<int> route; route.reserve(n);
    route.push_back(0); visited[0] = true;
    int current = 0;

    while ((int)route.size() < n) {
        vector<pair<int, int>> cands; // (distance, vertex)
        for (int v = 1; v < n; v++) if (!visited[v]) cands.push_back({eval.fEdgeDis[current][v], v});
        sort(cands.begin(), cands.end());
        int rclSize = min((int)cands.size(), alpha);
        uniform_int_distribution<int> d(0, rclSize - 1);
        int chosen = cands[d(gen)].second;
        route.push_back(chosen);
        visited[chosen] = true;
        current = chosen;
    }
    return route;
}

/* "local search: x' <- arg min Nk(x)" (Algorithms 3 and 4) means a full
   descent within Nk -- repeatedly apply the best move in Nk until none
   improves -- not a single move. A single move can't be compared
   meaningfully against a solution that was just heavily perturbed (see
   run_vns): only a full descent gives x'' a fair chance to recover past
   the pre-shake cost. Returns whether ANY move was applied. */
bool local_search_in_neighborhood(int nb, vector<int>& tour, Solution& sol,
                                   const vector<int>& farthest, int orOptMaxLen) {
    bool any = false;
    while (best_move_in_neighborhood(nb, tour, sol, farthest, orOptMaxLen)) any = true;
    return any;
}

/* Algorithm 3: VND -- deterministic descent, resets to the first
   neighborhood (in the paper's order: swap-adjacent, remove-insert,
   swap, 2-opt, or-opt) whenever a full descent within the current
   neighborhood found any improvement, stops when kmax consecutive
   non-improving neighborhoods are seen.

   orOptMaxLen defaults to 3 (the paper's original Or-opt, segment
   lengths 1-3). Passing a larger value (e.g. 6) additively extends the
   or-opt neighborhood to the longer segments this project confirmed as
   a real, statistically significant quality gain on top of GILS-RVND
   (H12a, docs/experiments/h12-extended-oropt.md) -- testing whether the
   same extension helps this different algorithm too. */
void run_vnd(vector<int>& tour, Evaluator& eval, const vector<int>& farthest, int orOptMaxLen) {
    int n = eval.Ncity;
    Solution sol; sol.Define(n); sol.fDist = eval.fEdgeDis;

    static const int order[N_NEIGHBORHOODS] = { SWAP_ADJACENT, REMOVE_INSERT, SWAP, TWO_OPT, OR_OPT };
    int k = 0;
    while (k < N_NEIGHBORHOODS) {
        bool improved = local_search_in_neighborhood(order[k], tour, sol, farthest, orOptMaxLen);
        if (improved) k = 0; else k++;
    }
}

/* Shaking move (Sect. 2.3): remove a fixed percentage of customers at
   random and reinsert each at an independent random position. */
void shake(vector<int>& tour, double pct, mt19937& gen) {
    int n = (int)tour.size();
    int nRemove = max(1, (int)llround(pct * (n - 1)));
    vector<int> positions(n - 1);
    iota(positions.begin(), positions.end(), 1);
    shuffle(positions.begin(), positions.end(), gen);
    positions.resize(nRemove);
    sort(positions.rbegin(), positions.rend()); // remove from the back first

    vector<int> removed;
    for (int p : positions) { removed.push_back(tour[p]); tour.erase(tour.begin() + p); }

    for (int v : removed) {
        uniform_int_distribution<int> d(1, (int)tour.size());
        int pos = d(gen);
        tour.insert(tour.begin() + pos, v);
    }
}

/* Algorithm 4: VNS -- same control flow as VND, but each neighborhood
   visit first shakes x (not x''), then runs a full descent in Nk from
   the shaken solution; only accepted if better than the pre-shake x.
   Does not require the reduction schemes. */
void run_vns(vector<int>& tour, Evaluator& eval, const vector<int>& farthest,
             double shakePct, int orOptMaxLen, mt19937& gen) {
    int n = eval.Ncity;
    Solution sol; sol.Define(n); sol.fDist = eval.fEdgeDis;
    static const int order[N_NEIGHBORHOODS] = { SWAP_ADJACENT, REMOVE_INSERT, SWAP, TWO_OPT, OR_OPT };

    int xCost = tour_cost(tour, eval.fEdgeDis);
    int k = 0;
    while (k < N_NEIGHBORHOODS) {
        vector<int> xPrime = tour;
        shake(xPrime, shakePct, gen);
        local_search_in_neighborhood(order[k], xPrime, sol, farthest, orOptMaxLen); // x'' regardless of accept
        int xppCost = tour_cost(xPrime, eval.fEdgeDis);
        if (xppCost < xCost) {
            tour = xPrime; xCost = xppCost; k = 0;
        } else {
            k++;
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./grasp_vnd <instance.tsp> [--alpha 2] [--restarts 10]\n";
        cerr << "    [--local-search vnd|vns] [--shake-pct 0.20] [--or-opt-max-len 3] [--seed N]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int alpha = 2;
    int restarts = 10;
    string localSearch = "vnd";
    double shakePct = 0.20;
    int orOptMaxLen = 3; // paper's original Or-opt (lengths 1-3); see H12a note above run_vnd
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--alpha" && i + 1 < argc) alpha = stoi(argv[++i]);
        else if (a == "--restarts" && i + 1 < argc) restarts = stoi(argv[++i]);
        else if (a == "--local-search" && i + 1 < argc) localSearch = argv[++i];
        else if (a == "--or-opt-max-len" && i + 1 < argc) orOptMaxLen = stoi(argv[++i]);
        else if (a == "--shake-pct" && i + 1 < argc) shakePct = stod(argv[++i]);
        else if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos) filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());
    int n = eval.Ncity;

    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());
    vector<int> farthest = compute_farthest(n, eval.fEdgeDis);

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    int bestCost = INT_MAX;
    vector<int> bestTour;

    for (int r = 0; r < restarts; r++) {
        vector<int> tour = construction_salehipour(eval, alpha, gen);
        if (localSearch == "vns") run_vns(tour, eval, farthest, shakePct, orOptMaxLen, gen);
        else run_vnd(tour, eval, farthest, orOptMaxLen);

        int cost = tour_cost(tour, eval.fEdgeDis);
        if (cost < bestCost) { bestCost = cost; bestTour = tour; }
    }

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << n << "\n";
    cout << "COST " << bestCost << "\n";
    cout << "ALPHA " << alpha << "\n";
    cout << "RESTARTS " << restarts << "\n";
    cout << "OR_OPT_MAX_LEN " << orOptMaxLen << "\n";
    cout << "LOCAL_SEARCH " << localSearch << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < n; i++) cout << bestTour[i] << ",\n"[i == n - 1];

    return 0;
}
