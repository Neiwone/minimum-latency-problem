#include "neighborhoods_cand.h"
#include <algorithm>
#include <vector>

using namespace std;

CandList make_candidate_list(const Evaluator& eval, int K) {
    CandList cl;
    cl.K    = min(K, min(eval.fNearNumMax, eval.Ncity - 1));
    cl.near = eval.fNearCity;
    return cl;
}

/* Rebuild fTour with [i..j] (optionally reversed) moved so that it sits
   immediately after the city currently at position k -- the same
   semantics evaluateOrOpt/evaluateOrOptReversed price. Scratch buffers
   are passed in so a scan does not reallocate per applied move. */
static void apply_oropt(Solution& sol, int i, int j, int k, bool reversed,
                        vector<int>& seg, vector<int>& rest) {
    int len = j - i + 1;
    int anchor = sol.fTour[k];

    seg.resize(len);
    for (int m = 0; m < len; m++)
        seg[m] = reversed ? sol.fTour[j - m] : sol.fTour[i + m];

    rest.clear();
    for (int m = 0; m < sol.fN; m++)
        if (m < i || m > j) rest.push_back(sol.fTour[m]);

    int pos = 0;
    for (int m = 0; m < (int)rest.size(); m++) {
        sol.fTour[pos++] = rest[m];
        if (rest[m] == anchor)
            for (int q = 0; q < len; q++) sol.fTour[pos++] = seg[q];
    }

    sol.calculateStructures();
}

/* One first-improvement pass over the pruned or-opt neighborhood.
   Returns true if a move was applied. */
static bool pass_oropt(Solution& sol, const CandList& cl, int len, bool reversed,
                       vector<int>& seg, vector<int>& rest) {
    const int n = sol.fN;

    for (int i = 1; i + len - 1 < n; i++) {
        int j = i + len - 1;
        int endpoints[2] = { sol.fTour[i], sol.fTour[j] };
        int nEnd = (len == 1) ? 1 : 2;

        for (int e = 0; e < nEnd; e++) {
            for (int t = 0; t < cl.K; t++) {
                int m  = cl.near[endpoints[e]][t];
                int pm = sol.posOf[m];

                /* insert right after m, and right before m */
                for (int d = 0; d < 2; d++) {
                    int k = pm - d;
                    if (k < 0 || k >= n) continue;
                    if (k >= i && k <= j) continue;

                    bool ok = reversed ? sol.evaluateOrOptReversed(i, j, k)
                                       : sol.evaluateOrOpt(i, j, k);
                    if (!ok) continue;

                    apply_oropt(sol, i, j, k, reversed, seg, rest);
                    return true;
                }
            }
        }
    }
    return false;
}

static bool pass_2opt(Solution& sol, const CandList& cl) {
    const int n = sol.fN;

    for (int i = 1; i < n; i++) {
        int a = sol.fTour[i - 1];

        for (int t = 0; t < cl.K; t++) {
            int j = sol.posOf[cl.near[a][t]];
            if (j <= i) continue;

            if (sol.evaluate2Opt(i, j)) {
                reverse(sol.fTour + i, sol.fTour + j + 1);
                sol.calculateStructures();
                return true;
            }
        }
    }
    return false;
}

static bool pass_swap(Solution& sol, const CandList& cl) {
    const int n = sol.fN;

    for (int i = 1; i < n; i++) {
        int a = sol.fTour[i - 1];

        for (int t = 0; t < cl.K; t++) {
            int j = sol.posOf[cl.near[a][t]];
            if (j == i || j < 1) continue;

            if (sol.evaluateSwap(i, j)) {
                swap(sol.fTour[i], sol.fTour[j]);
                sol.calculateStructures();
                return true;
            }
        }
    }
    return false;
}

void RVND_Candidate(Solution& sol, const CandList& cl, int maxLen,
                    bool useReversed, mt19937& gen) {
    /* Neighborhood ids: 0 = swap, 1 = 2-opt,
       2..(1+maxLen)            = or-opt forward, length id-1
       (2+maxLen)..             = or-opt reversed, length id-maxLen */
    const int nFwd = maxLen;
    const int nRev = useReversed ? max(0, maxLen - 1) : 0;
    const int total = 2 + nFwd + nRev;

    vector<int> seg, rest;
    rest.reserve(sol.fN);

    vector<int> NL(total);
    for (int i = 0; i < total; i++) NL[i] = i;

    while (!NL.empty()) {
        uniform_int_distribution<int> dist(0, (int)NL.size() - 1);
        int idx = dist(gen);
        int eta = NL[idx];

        int oldCost = sol.fEvaluationValue;

        if (eta == 0) {
            while (pass_swap(sol, cl)) {}
        } else if (eta == 1) {
            while (pass_2opt(sol, cl)) {}
        } else if (eta < 2 + nFwd) {
            int len = eta - 1;
            while (pass_oropt(sol, cl, len, false, seg, rest)) {}
        } else {
            int len = eta - (2 + nFwd) + 2;
            while (pass_oropt(sol, cl, len, true, seg, rest)) {}
        }

        if (sol.fEvaluationValue < oldCost) {
            NL.resize(total);
            for (int i = 0; i < total; i++) NL[i] = i;
        } else {
            NL.erase(NL.begin() + idx);
        }
    }
}
