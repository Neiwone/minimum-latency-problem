#ifndef __NEIGHBORHOODS_CAND__
#define __NEIGHBORHOODS_CAND__

#include "solution.h"
#include "evaluator.h"
#include <random>
#include <string>

/* Candidate-list RVND: only evaluate a move that creates an edge to one of
   the K nearest cities of the endpoint gaining a neighbour. O(n*K) scans. */

struct CandList {
    int   K;      /* neighbours considered per city */
    int** near;   /* near[city][t] = t-th nearest city (Evaluator::fNearCity) */
};

CandList make_candidate_list(const Evaluator& eval, int K);

/* Neighborhoods: swap, 2-opt, or-opt forward 1..maxLen, or-opt reversed
   2..maxLen. */
void RVND_Candidate(Solution& sol, const CandList& cl, int maxLen,
                    bool useReversed, std::mt19937& gen);

/* Don't-look bits. Re-arm rule for a latency objective: every city whose
   POSITION changed, plus junctions (why: h19-dlb-fast-regime.md 7.3). */
struct DlbState {
    std::vector<unsigned int> examined;  /* per city: bit set per neighborhood that failed */
    std::vector<char>         active;    /* per city: retired once `examined` fills up */
    int                       nActive = 0;

    void reset(int n);                                    /* arm every city */
    void arm_city(int c);
    void arm_range(const Solution& sol, int lo, int hi);   /* arm positions lo..hi */
};

void RVND_CandidateDLB(Solution& sol, const CandList& cl, int maxLen,
                       bool useReversed, std::mt19937& gen, DlbState& dlb);

/* Wider scans, both measured worse and OFF by default: or-opt anchors on
   the first F positions; 2-opt anchored on its second new edge too. */
void set_cand_opts(int frontAnchors, bool twoOptBothDirs);

/* Strict mode skips a (city, neighborhood) pair already failed, not just
   retired cities. OFF: 1.6x faster, same quality. */
void set_dlb_strict(bool strict);

/* Ablation: leave neighborhoods out of RVND_Candidate / RVND_CandidateDLB.
   Comma-separated names: swap, 2opt, oropt1..oropt<maxLen>, rev2..rev<maxLen>.
   Returns false (and leaves the set unchanged) on an unknown name. */
bool set_cand_disabled(const std::string& csv, int maxLen);

/* Per-neighborhood accounting for RVND_CandidateDLB: moves applied and cost
   removed, split by phase (0 = the descent from a fresh construction,
   1 = descents after a perturbation). Counting only; the search is the same. */
void nb_stats_set_phase(int phase);
void nb_stats_print();   /* NB_STATS <phase> <neighborhood> <moves> <gain> */

#endif
