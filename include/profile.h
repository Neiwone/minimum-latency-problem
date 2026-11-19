#ifndef __PROFILE__
#define __PROFILE__

#include <chrono>
#include <cstdio>

/* --profile: wall time spent in each phase of the GILS loop, to measure the
   share of the local search. A few clock reads per ILS iteration. */
struct PhaseTimes {
    double construction = 0, localSearch = 0, perturbation = 0;

    template <class F> static void add(double& acc, F&& f) {
        auto t0 = std::chrono::steady_clock::now();
        f();
        acc += std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    }

    void print(double totalSec) const {
        std::printf("PROFILE construction=%.3f local_search=%.3f perturbation=%.3f total=%.3f\n",
                    construction, localSearch, perturbation, totalSec);
    }
};

#endif
