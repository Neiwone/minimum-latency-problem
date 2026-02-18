#ifndef __SOLUTION__
#include "solution.h"
#endif

#include <cstring>


Solution::Solution() {
    fN = 0;
    fTour = NULL;
    fEvaluationValue = 0;
    fDist = NULL;
    x = NULL;
    y = NULL;
    T = C = Cr = NULL;
}

Solution::~Solution() {
    delete[] fTour;
    if (T != NULL) {
        for (int i = 0; i < fN; i++) {
            delete[] T[i];
            delete[] C[i];
            delete[] Cr[i];
        }
        delete[] T;
        delete[] C;
        delete[] Cr;
    }
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
    T = C = Cr = NULL;

    if (fN > 0) {
        fTour = new int[fN];
        memcpy(fTour, src.fTour, fN * sizeof(int));

        if (src.T != NULL)
            calculateStructures();
    } else {
        fTour = NULL;
    }
}

Solution& Solution::operator = (const Solution& src) {
    if (this == &src) return *this;

    if (fN != src.fN) {
        delete[] fTour;
        if (T != NULL) {
            for (int i = 0; i < fN; i++) {
                delete[] T[i];
                delete[] C[i];
                delete[] Cr[i];
            }
            delete[] T;  delete[] C;  delete[] Cr;
            T = C = Cr = NULL;
        }
        fN = src.fN;
        fTour = new int[fN];
    }

    memcpy(fTour, src.fTour, fN * sizeof(int));
    fEvaluationValue = src.fEvaluationValue;
    fDist = src.fDist;

    if (src.T != NULL)
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

    // Allocate matrices on first call
    if (T == NULL) {
        T  = new int*[fN];
        C  = new int*[fN];
        Cr = new int*[fN];
        for (int i = 0; i < fN; i++) {
            T[i]  = new int[fN];
            C[i]  = new int[fN];
            Cr[i] = new int[fN];
        }
    }

    int edge[fN];
    edge[0] = 0;
    for (int j = 1; j < fN; j++)
        edge[j] = fDist[fTour[j - 1]][fTour[j]];

    for (int i = 0; i < fN; i++) {
        T[i][i] = 0;
        C[i][i] = 0;

        for (int j = i + 1; j < fN; j++) {
            T[i][j] = T[i][j - 1] + edge[j];
            C[i][j] = C[i][j - 1] + T[i][j];
        }
    }

    for (int j = 0; j < fN; j++) {
        Cr[j][j] = 0;
        for (int i = j - 1; i >= 0; i--) {
            Cr[i][j] = Cr[i + 1][j] + T[i][j];
        }
    }

    fEvaluationValue = C[0][fN - 1];
}


void Solution::printAllSubsequences() {
    assert(T != NULL && C != NULL);

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
                 << setw(10) << T[i][j]
                 << setw(10) << C[i][j]
                 << setw(10) << getW(i, j)
                 << "\n";
        }
    }

    cout << "==================================================\n";
}

bool Solution::evaluateSwap(int i, int j) {
    if (i > j) swap(i, j);

    int t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = T[u][v];
        int Cu = C[u][v];
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        int e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    append(0, i - 1);
    append(j, j);
    append(i + 1, j - 1);
    append(i, i);
    append(j + 1, fN - 1);

    return c < fEvaluationValue;
}

bool Solution::evaluate2Opt(int i, int j) {
    if (i > j) swap(i, j);

    int t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = T[u][v];
        int Cu = C[u][v];
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        int e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    auto appendReversed = [&](int u, int v) {
        if (u > v) return;
        int Tu = T[u][v];
        int Cu = Cr[u][v];
        int Wu = getW(u, v);
        int firstNode = fTour[v];   /* reversed: first is tour[v] */
        int lastNode  = fTour[u];   /* reversed: last  is tour[u] */

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        int e = fDist[last][firstNode];
        c += Wu * (t + e) + Cu;
        t += e + Tu;
        last = lastNode;
    };

    append(0, i - 1);
    appendReversed(i, j);
    append(j + 1, fN - 1);

    return c < fEvaluationValue;
}

bool Solution::evaluateReinsertion(int i, int j) {
    if (i == j) return false;

    int t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = T[u][v];
        int Cu = C[u][v];
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        int e = fDist[last][firstNode];
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

    return c < fEvaluationValue;
}

bool Solution::evaluateOrOpt(int i, int j, int k) {
    if (i > j) swap(i, j);
    if (k >= i && k <= j) return false;

    int t = 0, c = 0;
    bool first = true;
    int last = -1;

    auto append = [&](int u, int v) {
        if (u > v) return;
        int Tu = T[u][v];
        int Cu = C[u][v];
        int Wu = getW(u, v);
        int firstNode = fTour[u];
        int lastNode  = fTour[v];

        if (first) {
            t = Tu; c = Cu;
            last = lastNode; first = false;
            return;
        }
        int e = fDist[last][firstNode];
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

    return c < fEvaluationValue;
}
