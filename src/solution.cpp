#ifndef __SOLUTION__
#include "solution.h"
#endif

#include <cstring>


static bool gClosedTour = false;

void set_closed_tour(bool on) { gClosedTour = on; }
bool closed_tour() { return gClosedTour; }



Solution::Solution() {
    fN = 0;
    fTour = NULL;
    fEvaluationValue = 0;
    fDist = NULL;
    x = NULL;
    y = NULL;
    P = SP = NULL;
    posOf = NULL;
}

Solution::~Solution() {
    delete[] fTour;
    delete[] P;
    delete[] SP;
    delete[] posOf;
}

void Solution::Define(int N) {
    fN = N;
    fTour = new int[fN];
}

Solution::Solution(const Solution& src) {
    fN = src.fN;
    fEvaluationValue = src.fEvaluationValue;
    fDist = src.fDist;
    x = NULL;
    y = NULL;
    P = SP = NULL;
    posOf = NULL;

    if (fN > 0) {
        fTour = new int[fN];
        memcpy(fTour, src.fTour, fN * sizeof(int));

        if (src.P != NULL)
            calculateStructures();
    } else {
        fTour = NULL;
    }
}

Solution& Solution::operator = (const Solution& src) {
    if (this == &src) return *this;

    if (fN != src.fN) {
        delete[] fTour;
        delete[] P;   P  = NULL;
        delete[] SP;  SP = NULL;
        delete[] posOf; posOf = NULL;
        fN = src.fN;
        fTour = new int[fN];
    }

    memcpy(fTour, src.fTour, fN * sizeof(int));
    fEvaluationValue = src.fEvaluationValue;
    fDist = src.fDist;

    if (src.P != NULL)
        calculateStructures();

    return *this;
}

bool Solution::operator == (const Solution& src) {
    if (fN != src.fN) return false;
    for (int i = 0; i < fN; i++) {
        if (fTour[i] != src.fTour[i]) return false;
    }
    return true;
}

void Solution::calculateStructures() {
    assert(fTour != NULL);
    assert(fDist != NULL);

    if (P == NULL) {
        P     = new long long[fN];
        SP    = new long long[fN];
        posOf = new int[fN];
    }

    P[0]  = 0;
    SP[0] = 0;
    posOf[fTour[0]] = 0;
    for (int j = 1; j < fN; j++) {
        P[j]  = P[j - 1] + fDist[fTour[j - 1]][fTour[j]];
        SP[j] = SP[j - 1] + P[j];
        posOf[fTour[j]] = j;
    }

    fEvaluationValue = getC(0, fN - 1);
    if (gClosedTour) fEvaluationValue += closingTerm(getT(0, fN - 1), fTour[fN - 1]);
}


void Solution::calculateStructuresFrom(int lo) {
    if (P == NULL || lo <= 0) { calculateStructures(); return; }
    if (lo >= fN) { calculateStructures(); return; }

    for (int j = lo; j < fN; j++) {
        P[j]  = P[j - 1] + fDist[fTour[j - 1]][fTour[j]];
        SP[j] = SP[j - 1] + P[j];
        posOf[fTour[j]] = j;
    }

    fEvaluationValue = getC(0, fN - 1);
    if (gClosedTour) fEvaluationValue += closingTerm(getT(0, fN - 1), fTour[fN - 1]);
}


void Solution::printAllSubsequences() {
    assert(P != NULL && SP != NULL);

    if (fN > 15) {
        cout << "Too many subsequences to print\n";
        return;
    }

    cout << "\n================ SUBSEQUENCE TABLE ================\n";
    cout << left
         << setw(20) << "Subsequence"
         << setw(10) << "T"
         << setw(10) << "C"
         << setw(10) << "W"
         << "\n";
    cout << string(50, '-') << "\n";

    for (int i = 0; i < fN; i++) {
        for (int j = i; j < fN; j++) {
            string seq = "(";
            for (int k = i; k <= j; k++) {
                seq += to_string(fTour[k]);
                if (k < j) seq += ",";
            }
            seq += ")";

            cout << left
                 << setw(20) << seq
                 << setw(10) << getT(i, j)
                 << setw(10) << getC(i, j)
                 << setw(10) << getW(i, j)
                 << "\n";
        }
    }

    cout << "==================================================\n";
}

bool Solution::evaluateSwap(int i, int j) {
    if (i > j) swap(i, j);

    Cost t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getC(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    append(0, i - 1);
    append(j, j);
    append(i + 1, j - 1);
    append(i, i);
    append(j + 1, fN - 1);

    if (gClosedTour) c += closingTerm(t, last);
    return c < fEvaluationValue;
}

bool Solution::evaluate2Opt(int i, int j) {
    if (i > j) swap(i, j);

    Cost t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getC(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    auto appendReversed = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getCr(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[v];   /* reversed: first is tour[v] */
        int lastNode  = fTour[u];   /* reversed: last  is tour[u] */

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    append(0, i - 1);
    appendReversed(i, j);
    append(j + 1, fN - 1);

    if (gClosedTour) c += closingTerm(t, last);
    return c < fEvaluationValue;
}

bool Solution::evaluateReinsertion(int i, int j) {
    if (i == j) return false;

    Cost t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getC(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    if (i < j) {
        append(0, i - 1);
        append(i + 1, j);
        append(i, i);
        append(j + 1, fN - 1);
    } else {
        append(0, j);
        append(i, i);
        append(j + 1, i - 1);
        append(i + 1, fN - 1);
    }

    if (gClosedTour) c += closingTerm(t, last);
    return c < fEvaluationValue;
}

bool Solution::evaluateThreeOptDoubleReversal(int i, int j, int k) {
    Cost t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getC(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    auto appendReversed = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getCr(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[v];
        int lastNode  = fTour[u];
        if (first) { t = Tu; c = Cu; last = lastNode; first = false; return; }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    append(0, i);
    appendReversed(i + 1, j);
    appendReversed(j + 1, k);
    append(k + 1, fN - 1);

    if (gClosedTour) c += closingTerm(t, last);
    return c < fEvaluationValue;
}

bool Solution::evaluateOrOpt(int i, int j, int k) {
    if (i > j) swap(i, j);
    if (k >= i && k <= j) return false;

    Cost t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getC(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    if (k < i) {
        append(0, k);
        append(i, j);
        append(k + 1, i - 1);
        append(j + 1, fN - 1);
    } else {
        append(0, i - 1);
        append(j + 1, k);
        append(i, j);
        append(k + 1, fN - 1);
    }

    if (gClosedTour) c += closingTerm(t, last);
    return c < fEvaluationValue;
}


bool Solution::evaluateOrOptReversed(int i, int j, int k) {
    if (i > j) swap(i, j);
    if (k >= i && k <= j) return false;

    Cost t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getC(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    auto appendReversed = [&](int u, int v) {
        if (u > v) return;
        Cost Tu = getT(u, v);
        Cost Cu = getCr(u, v);
        int Wu = getW(u, v);
        int firstNode = fTour[v];
        int lastNode  = fTour[u];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        Cost e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    if (k < i) {
        append(0, k);
        appendReversed(i, j);
        append(k + 1, i - 1);
        append(j + 1, fN - 1);
    } else {
        append(0, i - 1);
        append(j + 1, k);
        appendReversed(i, j);
        append(k + 1, fN - 1);
    }

    if (gClosedTour) c += closingTerm(t, last);
    return c < fEvaluationValue;
}
