#ifndef __RVND_ADAPTIVE__
#define __RVND_ADAPTIVE__

#include "solution.h"
#include <random>
#include <string>
#include <vector>

/* H15: or-opt lengths picked by roulette on learned weights, ceiling kMax
   moving with the frontier hit rate. State is per RUN, not per call. */
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

    /* Per-length attempts/hits/weight plus the kMax range, for -v. */
    std::string summary() const;
};

void RVND_AdaptiveOrOpt(Solution& sol, std::mt19937& gen, AdaptiveOrOptState& st);

#endif
