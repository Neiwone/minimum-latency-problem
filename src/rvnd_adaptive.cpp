#include "rvnd_adaptive.h"
#include "neighborhoods.h"

#include <algorithm>
#include <sstream>
#include <iomanip>

using namespace std;

/* Always in the list at weight 1.0, never adapted. Reinsertion is or-opt
   of length 1, so only lengths 2..kMax are learned. */
namespace {

enum FixedKind { FIX_SWAP = 0, FIX_2OPT = 1, FIX_REINSERTION = 2, FIX_COUNT = 3 };

void run_fixed(int kind, Solution& sol) {
    if (kind == FIX_SWAP) neighborhood_swap(sol);
    else if (kind == FIX_2OPT) neighborhood_2opt(sol);
    else neighborhood_reinsertion(sol);
}

/* An entry in the neighborhood list: either one of the fixed structures
   or an or-opt of a specific segment length. */
struct Entry {
    bool isOrOpt;
    int  value; /* FixedKind when !isOrOpt, else the segment length */
};

} // namespace

AdaptiveOrOptState::AdaptiveOrOptState() {
    weight.assign(K_CAP + 1, 0.0);
    credit.assign(K_CAP + 1, 0.0);
    attempts.assign(K_CAP + 1, 0);
    hits.assign(K_CAP + 1, 0);
    totalAttempts.assign(K_CAP + 1, 0);
    totalHits.assign(K_CAP + 1, 0);
    totalGain.assign(K_CAP + 1, 0.0);

    for (int L = 2; L <= kMax; L++) weight[L] = 1.0;
    kMaxMinSeen = kMax;
    kMaxMaxSeen = kMax;
}

/* Rebalance weights and move the ceiling, every `period` scans -- pooled
   over many convergences, since one gives far too few scans to estimate. */
static void adapt(AdaptiveOrOptState& st) {
    st.adaptations++;

    /* reward = credit/attempts, normalized by the best length. Lengths
       with no attempts this period keep their weight. */
    double bestReward = 0.0;
    vector<double> reward(st.weight.size(), -1.0);
    for (int L = 2; L <= st.kMax; L++) {
        if (st.attempts[L] <= 0) continue;
        reward[L] = st.credit[L] / (double)st.attempts[L];
        bestReward = max(bestReward, reward[L]);
    }

    if (bestReward > 0.0) {
        for (int L = 2; L <= st.kMax; L++) {
            if (reward[L] < 0.0) continue; /* untried this period */
            double target = reward[L] / bestReward;
            st.weight[L] = (1.0 - st.rho) * st.weight[L] + st.rho * target;
            st.weight[L] = max(st.weight[L], st.weightFloor);
        }
    }

    /* Driven by the frontier (the largest enabled lengths), not the
       average: what matters is whether the longest still find anything. */
    int frontierLo = max(2, st.kMax - 1);
    long fAttempts = 0, fHits = 0;
    for (int L = frontierLo; L <= st.kMax; L++) {
        fAttempts += st.attempts[L];
        fHits += st.hits[L];
    }

    if (fAttempts > 0) {
        double fRate = (double)fHits / (double)fAttempts;
        if (fRate >= st.growHitRate && st.kMax < AdaptiveOrOptState::K_CAP) {
            st.kMax++;
            st.weight[st.kMax] = st.newWeight; /* optimistic: give it a fair trial */
        } else if (fRate <= st.shrinkHitRate && st.kMax > AdaptiveOrOptState::K_FLOOR) {
            st.weight[st.kMax] = 0.0;
            st.kMax--;
        }
        st.kMaxMinSeen = min(st.kMaxMinSeen, st.kMax);
        st.kMaxMaxSeen = max(st.kMaxMaxSeen, st.kMax);
    }

    fill(st.credit.begin(), st.credit.end(), 0.0);
    fill(st.attempts.begin(), st.attempts.end(), 0L);
    fill(st.hits.begin(), st.hits.end(), 0L);
    st.scansThisPeriod = 0;
}

void RVND_AdaptiveOrOpt(Solution& sol, mt19937& gen, AdaptiveOrOptState& st) {
    vector<Entry> NL;

    auto rebuild = [&]() {
        NL.clear();
        for (int k = 0; k < FIX_COUNT; k++) NL.push_back({false, k});
        for (int L = 2; L <= st.kMax; L++) NL.push_back({true, L});
    };

    rebuild();

    while (!NL.empty()) {
        /* Roulette wheel over the current list: fixed structures weigh
           1.0, or-opt lengths weigh what they have learned. */
        double total = 0.0;
        for (const Entry& e : NL)
            total += e.isOrOpt ? max(st.weight[e.value], st.weightFloor) : 1.0;

        uniform_real_distribution<double> pick(0.0, total);
        double target = pick(gen);

        int idx = (int)NL.size() - 1;
        double acc = 0.0;
        for (int i = 0; i < (int)NL.size(); i++) {
            acc += NL[i].isOrOpt ? max(st.weight[NL[i].value], st.weightFloor) : 1.0;
            if (target <= acc) { idx = i; break; }
        }

        Entry chosen = NL[idx];
        Cost oldCost = sol.fEvaluationValue;

        if (chosen.isOrOpt) neighborhood_oropt_len(sol, chosen.value);
        else run_fixed(chosen.value, sol);

        bool improved = sol.fEvaluationValue < oldCost;

        if (chosen.isOrOpt) {
            int L = chosen.value;
            st.attempts[L]++;
            st.totalAttempts[L]++;
            if (improved) {
                double gainRel = oldCost > 0
                    ? (double)(oldCost - sol.fEvaluationValue) / (double)oldCost
                    : 0.0;
                st.credit[L] += 1.0 + st.gainScale * gainRel;
                st.hits[L]++;
                st.totalHits[L]++;
                st.totalGain[L] += gainRel;
            }
            st.scansThisPeriod++;
            if (st.scansThisPeriod >= st.period) adapt(st);
        }

        if (improved) {
            /* Same rule as RVND(): any improvement re-enables everything.
               rebuild() also picks up a kMax that adapt() just changed. */
            rebuild();
        } else {
            /* Also drop lengths above the ceiling, in case adapt() just
               shrank kMax and left disabled lengths in the list. */
            NL.erase(NL.begin() + idx);
            NL.erase(remove_if(NL.begin(), NL.end(), [&](const Entry& e) {
                         return e.isOrOpt && e.value > st.kMax;
                     }), NL.end());
        }
    }
}

string AdaptiveOrOptState::summary() const {
    ostringstream os;
    os << "adaptive-oropt: kMax final=" << kMax
       << " (visitado " << kMaxMinSeen << ".." << kMaxMaxSeen << ")"
       << " adaptacoes=" << adaptations << "\n";
    os << fixed << setprecision(4);
    for (int L = 2; L <= K_CAP; L++) {
        if (totalAttempts[L] == 0) continue;
        double rate = (double)totalHits[L] / (double)totalAttempts[L];
        os << "  oropt" << setw(2) << L
           << "  scans=" << setw(8) << totalAttempts[L]
           << "  hits=" << setw(7) << totalHits[L]
           << "  hit_rate=" << setw(7) << rate
           << "  ganho_medio_rel=" << setw(8)
           << (totalHits[L] ? totalGain[L] / (double)totalHits[L] : 0.0)
           << "  peso_final=" << setw(7) << weight[L]
           << (L > kMax ? "  (desativado)" : "")
           << "\n";
    }
    return os.str();
}
