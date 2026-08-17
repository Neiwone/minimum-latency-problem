#include "construction.h"
#include <algorithm>

using namespace std;

void construction(Solution& sol, Evaluator& eval, double alpha, mt19937& gen) {
    int n = eval.Ncity;

    vector<int> CL;
    for (int i = 1; i < n; i++)
        CL.push_back(i);

    vector<int> route;
    route.push_back(0);

    int r = 0;

    while (!CL.empty()) {
        sort(CL.begin(), CL.end(), [&](int a, int b) {
            return eval.fEdgeDis[r][a] < eval.fEdgeDis[r][b];
        });

        int rclSize = max(1, (int)(alpha * CL.size()));
        uniform_int_distribution<int> dist(0, rclSize - 1);

        int idx = dist(gen);
        int c = CL[idx];

        route.push_back(c);
        r = c;

        CL.erase(CL.begin() + idx);
    }

    sol.Define(n);
    sol.fDist = eval.fEdgeDis;
    for (int i = 0; i < n; i++)
        sol.fTour[i] = route[i];

    sol.calculateStructures();
}

/* Cumulative cost of the hypothetical segment r -> c -> (k-1 more
   nearest-unvisited hops), used to score candidate c during
   construction_lookahead(). `used` marks nodes already placed in the
   route so far (not including c); this function does not mutate it. */
static int lookahead_score(Evaluator& eval, int r, int c, const vector<bool>& used, int k) {
    vector<bool> avail = used;
    avail[c] = true;

    int cur = c;
    int running = eval.fEdgeDis[r][c];
    int total = running;

    for (int step = 1; step < k; step++) {
        int best = -1, bestDist = INT_MAX;
        for (int cand = 1; cand < eval.Ncity; cand++) {
            if (avail[cand]) continue;
            int d = eval.fEdgeDis[cur][cand];
            if (d < bestDist) { bestDist = d; best = cand; }
        }
        if (best == -1) break;
        running += bestDist;
        total += running;
        avail[best] = true;
        cur = best;
    }
    return total;
}

void construction_lookahead(Solution& sol, Evaluator& eval, double alpha, int k, mt19937& gen) {
    int n = eval.Ncity;

    vector<bool> used(n, false);
    used[0] = true;

    vector<int> CL;
    for (int i = 1; i < n; i++)
        CL.push_back(i);

    vector<int> route;
    route.push_back(0);

    int r = 0;

    while (!CL.empty()) {
        vector<pair<int, int>> scored; // (score, node)
        scored.reserve(CL.size());
        for (int c : CL)
            scored.push_back({lookahead_score(eval, r, c, used, k), c});

        sort(scored.begin(), scored.end());

        int rclSize = max(1, (int)(alpha * scored.size()));
        uniform_int_distribution<int> dist(0, rclSize - 1);

        int idx = dist(gen);
        int c = scored[idx].second;

        route.push_back(c);
        used[c] = true;
        r = c;

        CL.erase(find(CL.begin(), CL.end(), c));
    }

    sol.Define(n);
    sol.fDist = eval.fEdgeDis;
    for (int i = 0; i < n; i++)
        sol.fTour[i] = route[i];

    sol.calculateStructures();
}
