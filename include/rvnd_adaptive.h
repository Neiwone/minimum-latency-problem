#ifndef __RVND_ADAPTIVE__
#define __RVND_ADAPTIVE__

#include "solution.h"
#include <random>
#include <string>
#include <vector>

/* Adaptive-or-opt RVND.

   Motivation: RVND_ExtendedOrOpt (H12a, the one real quality finding of
   this project) hard-wires or-opt segment lengths 2..6 and scans all of
   them with equal probability, forever. Two things are left on the table:

     1. The useful ceiling is not the same for every instance or for every
        phase of the search -- early on, when the tour is far from a local
        optimum, short segments pay off; later, the improvements that
        remain tend to need longer relocations. A fixed k_max=6 both
        over-scans (paying O(n^2) for lengths that stopped producing) and
        under-scans (never trying 7..10 when they would still pay).
     2. Within the ceiling, lengths are not equally productive, but plain
        RVND visits them uniformly at random.

   This RVND makes the or-opt ceiling `kMax` an adaptive parameter and
   biases selection toward the lengths that are actually producing
   improvements ("the ones that most need to be visited"):

     - Selection: the neighborhood list holds the three fixed structures
       (swap, 2-opt, reinsertion, i.e. or-opt of length 1) plus one entry
       per or-opt length in [2, kMax]. The next structure to scan is drawn
       by roulette wheel: fixed structures keep weight 1.0, each or-opt
       length carries its learned weight.
     - Credit: every scan is an attempt; an improving scan earns
       1 + gainScale * (relative cost improvement). Reward per length is
       credit/attempts over the current period.
     - Adaptation (every `period` scans, accumulated ACROSS RVND calls so
       learning survives the hundreds/thousands of convergences an ILS
       run performs): weights are smoothed toward the observed reward,
       w <- (1-rho)*w + rho*reward_normalized, with a floor so no length
       is permanently starved; then the ceiling moves -- if the frontier
       lengths (the largest ones currently enabled) are still hitting
       above `growHitRate`, kMax grows by one (up to K_CAP, the new length
       entering with an optimistic weight so it gets a fair trial); if
       they hit below `shrinkHitRate`, kMax shrinks by one (never below
       K_FLOOR), so the search stops paying for scans that no longer
       produce.

   Termination is unchanged from RVND(): the scan stops once every
   structure currently in the list has failed to improve, so the result
   is still a local optimum with respect to the enabled neighborhoods.

   The state is owned by the caller (one instance per algorithm run, NOT
   per RVND call) -- see src/gils_am_rvnd.cpp --rvnd-mode adaptive-oropt. */
struct AdaptiveOrOptState {
    static const int K_FLOOR = 3;  /* never shrink the ceiling below this (the paper's original) */
    static const int K_CAP   = 12; /* never grow past this */

    /* --- tunables (defaults are the ones used in the experiments) --- */
    int    period        = 400;   /* scans between adaptations */
    double rho           = 0.30;  /* weight smoothing rate */
    double weightFloor   = 0.05;  /* minimum selection weight */
    double gainScale     = 50.0;  /* credit multiplier on relative improvement */
    double growHitRate   = 0.10;  /* frontier hit rate above which kMax grows */
    double shrinkHitRate = 0.02;  /* frontier hit rate below which kMax shrinks */
    double newWeight     = 1.0;   /* optimistic weight for a newly opened length */

    /* --- live state --- */
    int kMax = 6;                 /* current adaptive ceiling (starts at H12a's value) */
    std::vector<double> weight;   /* indexed by segment length, 0..K_CAP */
    std::vector<double> credit;   /* credit earned this period */
    std::vector<long>   attempts; /* scans this period */
    std::vector<long>   hits;     /* improving scans this period */
    long scansThisPeriod = 0;

    /* --- cumulative stats, for reporting (not used by the policy) --- */
    std::vector<long> totalAttempts;
    std::vector<long> totalHits;
    std::vector<double> totalGain; /* summed relative improvement */
    long adaptations = 0;
    int  kMaxMinSeen = 6;
    int  kMaxMaxSeen = 6;

    AdaptiveOrOptState();

    /* One line per or-opt length: attempts, hits, hit rate, final weight,
       plus the kMax range visited. Printed under -v by the solvers. */
    std::string summary() const;
};

void RVND_AdaptiveOrOpt(Solution& sol, std::mt19937& gen, AdaptiveOrOptState& st);

#endif
