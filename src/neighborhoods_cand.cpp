#include "neighborhoods_cand.h"
#include <algorithm>
#include <cstdio>
#include <set>
#include <sstream>
#include <vector>

using namespace std;

/* ---- Ablation: neighborhoods left out of the RVND ----------------- */

static set<string> g_disabled;

/* ids: 0 swap, 1 2-opt, 2..1+nFwd or-opt forward (len id-1), then or-opt
   reversed (len id-nFwd). */
static string nbhd_name(int eta, int nFwd) {
    if (eta == 0) return "swap";
    if (eta == 1) return "2opt";
    if (eta < 2 + nFwd) return "oropt" + to_string(eta - 1);
    return "rev" + to_string(eta - (2 + nFwd) + 2);
}

static vector<int> enabled_ids(int total, int nFwd) {
    vector<int> ids;
    for (int i = 0; i < total; i++)
        if (!g_disabled.count(nbhd_name(i, nFwd))) ids.push_back(i);
    return ids;
}

static long long g_nbMoves[2][32], g_nbGain[2][32];
static int g_nbPhase = 0, g_nbTotal = 0, g_nbFwd = 0;

void nb_stats_set_phase(int phase) { g_nbPhase = phase; }

void nb_stats_print() {
    for (int ph = 0; ph < 2; ph++)
        for (int eta = 0; eta < g_nbTotal; eta++)
            printf("NB_STATS %d %s %lld %lld\n", ph, nbhd_name(eta, g_nbFwd).c_str(),
                   g_nbMoves[ph][eta], g_nbGain[ph][eta]);
}

bool set_cand_disabled(const string& csv, int maxLen) {
    set<string> valid = { "swap", "2opt" };
    for (int L = 1; L <= maxLen; L++) valid.insert("oropt" + to_string(L));
    for (int L = 2; L <= maxLen; L++) valid.insert("rev" + to_string(L));

    set<string> names;
    stringstream ss(csv);
    string tok;
    while (getline(ss, tok, ','))
        if (!tok.empty()) {
            if (!valid.count(tok)) return false;
            names.insert(tok);
        }
    g_disabled = names;
    return true;
}

CandList make_candidate_list(const Evaluator& eval, int K) {
    CandList cl;
    cl.K    = min(K, min(eval.fNearNumMax, eval.Ncity - 1));
    cl.near = eval.fNearCity;
    return cl;
}

/* Move [i..j] (optionally reversed) after the city at position k. Scratch
   buffers are passed in so a scan does not reallocate per move. */
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

/* One sweep, returning how many moves it applied. It carries on after a
   move instead of restarting: O(n*K) per sweep, not per move. */
static int pass_oropt(Solution& sol, const CandList& cl, int len, bool reversed,
                      vector<int>& seg, vector<int>& rest) {
    const int n = sol.fN;
    int applied = 0;

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
                    applied++;
                    goto nextPosition;
                }
            }
        }
        nextPosition: ;
    }
    return applied;
}

static int pass_2opt(Solution& sol, const CandList& cl) {
    const int n = sol.fN;
    int applied = 0;

    for (int i = 1; i < n; i++) {
        int a = sol.fTour[i - 1];

        for (int t = 0; t < cl.K; t++) {
            int j = sol.posOf[cl.near[a][t]];
            if (j <= i) continue;

            if (sol.evaluate2Opt(i, j)) {
                reverse(sol.fTour + i, sol.fTour + j + 1);
                sol.calculateStructures();
                applied++;
                break;
            }
        }
    }
    return applied;
}

static int pass_swap(Solution& sol, const CandList& cl) {
    const int n = sol.fN;
    int applied = 0;

    for (int i = 1; i < n; i++) {
        int a = sol.fTour[i - 1];

        for (int t = 0; t < cl.K; t++) {
            int j = sol.posOf[cl.near[a][t]];
            if (j == i || j < 1) continue;

            if (sol.evaluateSwap(i, j)) {
                swap(sol.fTour[i], sol.fTour[j]);
                sol.calculateStructures();
                applied++;
                break;
            }
        }
    }
    return applied;
}

void RVND_Candidate(Solution& sol, const CandList& cl, int maxLen,
                    bool useReversed, mt19937& gen) {
    /* ids: 0 swap, 1 2-opt, 2..1+maxLen or-opt forward (len id-1),
       then or-opt reversed (len id-maxLen). */
    const int nFwd = maxLen;
    const int nRev = useReversed ? max(0, maxLen - 1) : 0;
    const int total = 2 + nFwd + nRev;

    vector<int> seg, rest;
    rest.reserve(sol.fN);

    const vector<int> all = enabled_ids(total, nFwd);
    vector<int> NL = all;

    while (!NL.empty()) {
        uniform_int_distribution<int> dist(0, (int)NL.size() - 1);
        int idx = dist(gen);
        int eta = NL[idx];

        Cost oldCost = sol.fEvaluationValue;

        if (eta == 0) {
            while (pass_swap(sol, cl) > 0) {}
        } else if (eta == 1) {
            while (pass_2opt(sol, cl) > 0) {}
        } else if (eta < 2 + nFwd) {
            int len = eta - 1;
            while (pass_oropt(sol, cl, len, false, seg, rest) > 0) {}
        } else {
            int len = eta - (2 + nFwd) + 2;
            while (pass_oropt(sol, cl, len, true, seg, rest) > 0) {}
        }

        if (sol.fEvaluationValue < oldCost) {
            NL = all;
        } else {
            NL.erase(NL.begin() + idx);
        }
    }
}

/* ---- Don't-look bits over the same pruned neighborhoods ---------- */

static int  g_frontAnchors   = 0;
static bool g_twoOptBothDirs = false;
static bool g_dlbStrict      = false;

void set_dlb_strict(bool strict) { g_dlbStrict = strict; }

void set_cand_opts(int frontAnchors, bool twoOptBothDirs) {
    g_frontAnchors   = frontAnchors;
    g_twoOptBothDirs = twoOptBothDirs;
}

void DlbState::reset(int n) {
    examined.assign(n, 0u);
    active.assign(n, 1);
    nActive = n;
}

void DlbState::arm_city(int c) {
    examined[c] = 0u;
    if (!active[c]) { active[c] = 1; nActive++; }
}

void DlbState::arm_range(const Solution& sol, int lo, int hi) {
    if (lo < 0) lo = 0;
    if (hi > sol.fN - 1) hi = sol.fN - 1;
    for (int p = lo; p <= hi; p++) arm_city(sol.fTour[p]);
}

/* A city retires only once every neighborhood failed on it. */
static inline void dlb_fail(DlbState& d, int c, unsigned bit, unsigned full) {
    if (!d.active[c]) return;
    d.examined[c] |= bit;
    if (d.examined[c] == full) { d.active[c] = 0; d.nActive--; }
}

/* Same relocation in O(span): a rotation of the affected range, prefix
   sums re-derived from the first disturbed position (returned). */
static int apply_oropt_fast(Solution& sol, int i, int j, int k, bool reversed) {
    int len = j - i + 1;
    if (reversed) reverse(sol.fTour + i, sol.fTour + j + 1);

    int lo;
    if (k < i) {
        rotate(sol.fTour + k + 1, sol.fTour + i, sol.fTour + j + 1);
        lo = k + 1;
    } else {
        rotate(sol.fTour + i, sol.fTour + j + 1, sol.fTour + k + 1);
        lo = i;
    }
    (void)len;

    sol.calculateStructuresFrom(lo);
    return lo;
}

static int pass_oropt_dlb(Solution& sol, const CandList& cl, int len, bool reversed,
                          DlbState& dlb, unsigned bit, unsigned full) {
    const int n = sol.fN;
    int applied = 0;

    for (int i = 1; i + len - 1 < n; i++) {
        int j = i + len - 1;
        int ci = sol.fTour[i], cj = sol.fTour[j];
        bool lookI = dlb.active[ci] && !(g_dlbStrict && (dlb.examined[ci] & bit));
        bool lookJ = len > 1 && dlb.active[cj] && !(g_dlbStrict && (dlb.examined[cj] & bit));
        if (!lookI && !lookJ) continue;

        int endpoints[2] = { ci, cj };
        int nEnd = (len == 1) ? 1 : 2;

        for (int e = 0; e < nEnd; e++) {
            for (int t = 0; t < cl.K; t++) {
                int m  = cl.near[endpoints[e]][t];
                int pm = sol.posOf[m];

                for (int d = 0; d < 2; d++) {
                    int k = pm - d;
                    if (k < 0 || k >= n) continue;
                    if (k >= i && k <= j) continue;

                    bool ok = reversed ? sol.evaluateOrOptReversed(i, j, k)
                                       : sol.evaluateOrOpt(i, j, k);
                    if (!ok) continue;

                    int hi = (k < i) ? j : k;
                    int lo = apply_oropt_fast(sol, i, j, k, reversed);
                    dlb.arm_range(sol, lo - 1, hi + 1);
                    applied++;
                    goto nextPosition;
                }
            }
        }

        /* Front anchors: reinsertions near the head of the tour, which
           geometric pruning is blind to. Off by default. */
        for (int k = 0; k < g_frontAnchors && k < n; k++) {
            if (k >= i && k <= j) continue;

            bool ok = reversed ? sol.evaluateOrOptReversed(i, j, k)
                               : sol.evaluateOrOpt(i, j, k);
            if (!ok) continue;

            int hi = (k < i) ? j : k;
            int lo = apply_oropt_fast(sol, i, j, k, reversed);
            dlb.arm_range(sol, lo - 1, hi + 1);
            applied++;
            goto nextPosition;
        }
        dlb_fail(dlb, ci, bit, full);
        if (len > 1) dlb_fail(dlb, cj, bit, full);
        nextPosition: ;
    }
    return applied;
}

static int pass_2opt_dlb(Solution& sol, const CandList& cl,
                         DlbState& dlb, unsigned bit, unsigned full) {
    const int n = sol.fN;
    int applied = 0;

    for (int i = 1; i < n; i++) {
        int a = sol.fTour[i - 1];
        if (!dlb.active[a]) continue;
        if (g_dlbStrict && (dlb.examined[a] & bit)) continue;

        bool moved = false;
        for (int t = 0; t < cl.K; t++) {
            int j = sol.posOf[cl.near[a][t]];
            if (j <= i) continue;

            if (sol.evaluate2Opt(i, j)) {
                reverse(sol.fTour + i, sol.fTour + j + 1);
                sol.calculateStructuresFrom(i);
                dlb.arm_range(sol, i - 1, j + 1);
                applied++;
                moved = true;
                break;
            }
        }

        /* Anchor on the other new edge, (tour[i], tour[j+1]). Off by default. */
        if (!moved && g_twoOptBothDirs) {
            int b = sol.fTour[i];
            for (int t = 0; t < cl.K; t++) {
                int j = sol.posOf[cl.near[b][t]] - 1;
                if (j <= i || j >= n) continue;

                if (sol.evaluate2Opt(i, j)) {
                    reverse(sol.fTour + i, sol.fTour + j + 1);
                    sol.calculateStructuresFrom(i);
                    dlb.arm_range(sol, i - 1, j + 1);
                    applied++;
                    moved = true;
                    break;
                }
            }
        }
        if (!moved) dlb_fail(dlb, a, bit, full);
    }
    return applied;
}

static int pass_swap_dlb(Solution& sol, const CandList& cl,
                         DlbState& dlb, unsigned bit, unsigned full) {
    const int n = sol.fN;
    int applied = 0;

    for (int i = 1; i < n; i++) {
        int a = sol.fTour[i - 1];
        if (!dlb.active[a]) continue;
        if (g_dlbStrict && (dlb.examined[a] & bit)) continue;

        bool moved = false;
        for (int t = 0; t < cl.K; t++) {
            int j = sol.posOf[cl.near[a][t]];
            if (j == i || j < 1) continue;

            if (sol.evaluateSwap(i, j)) {
                swap(sol.fTour[i], sol.fTour[j]);
                sol.calculateStructuresFrom(min(i, j));
                dlb.arm_range(sol, min(i, j) - 1, min(i, j) + 1);
                dlb.arm_range(sol, max(i, j) - 1, max(i, j) + 1);
                applied++;
                moved = true;
                break;
            }
        }
        if (!moved) dlb_fail(dlb, a, bit, full);
    }
    return applied;
}

void RVND_CandidateDLB(Solution& sol, const CandList& cl, int maxLen,
                       bool useReversed, mt19937& gen, DlbState& dlb) {
    const int nFwd = maxLen;
    const int nRev = useReversed ? max(0, maxLen - 1) : 0;
    const int total = 2 + nFwd + nRev;
    vector<int> NL = enabled_ids(total, nFwd);
    unsigned full = 0u;
    for (int eta : NL) full |= 1u << eta;

    if ((int)dlb.active.size() != sol.fN) dlb.reset(sol.fN);
    g_nbTotal = total;
    g_nbFwd = nFwd;

    while (dlb.nActive > 0) {
        shuffle(NL.begin(), NL.end(), gen);
        bool progressed = false;

        for (int eta : NL) {
            unsigned bit = 1u << eta;
            int got = 0, k;
            long long moves = 0;
            const Cost before = sol.fEvaluationValue;
            if (eta == 0) {
                while ((k = pass_swap_dlb(sol, cl, dlb, bit, full)) > 0) { got = 1; moves += k; }
            } else if (eta == 1) {
                while ((k = pass_2opt_dlb(sol, cl, dlb, bit, full)) > 0) { got = 1; moves += k; }
            } else if (eta < 2 + nFwd) {
                int len = eta - 1;
                while ((k = pass_oropt_dlb(sol, cl, len, false, dlb, bit, full)) > 0) { got = 1; moves += k; }
            } else {
                int len = eta - (2 + nFwd) + 2;
                while ((k = pass_oropt_dlb(sol, cl, len, true, dlb, bit, full)) > 0) { got = 1; moves += k; }
            }
            if (got) {
                progressed = true;
                g_nbMoves[g_nbPhase][eta] += moves;
                g_nbGain[g_nbPhase][eta] += before - sol.fEvaluationValue;
            }
            if (dlb.nActive == 0) break;
        }

        /* A round with no move means local optimum. Some bits never fill
           up (no or-opt anchors on the depot), so retire by hand. */
        if (!progressed) {
            for (int c = 0; c < sol.fN; c++) dlb.active[c] = 0;
            dlb.nActive = 0;
            break;
        }
    }
}
