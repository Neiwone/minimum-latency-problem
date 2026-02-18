#include "neighborhoods.h"
#include <algorithm>

using namespace std;

void neighborhood_swap(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN; i++) {
            for (int j = i + 1; j < sol.fN; j++) {
                if (sol.evaluateSwap(i, j)) {
                    swap(sol.fTour[i], sol.fTour[j]);
                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_reinsertion(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN; i++) {
            for (int j = 1; j < sol.fN; j++) {
                if (i == j) continue;

                if (sol.evaluateReinsertion(i, j)) {
                    int node = sol.fTour[i];

                    if (i < j) {
                        for (int k = i; k < j; k++)
                            sol.fTour[k] = sol.fTour[k + 1];

                        sol.fTour[j] = node;
                    }
                    else {
                        for (int k = i; k > j + 1; k--)
                            sol.fTour[k] = sol.fTour[k - 1];

                        sol.fTour[j + 1] = node;
                    }

                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_2opt(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN; i++) {
            for (int j = i + 1; j < sol.fN; j++) {
                if (sol.evaluate2Opt(i, j)) {
                    reverse(sol.fTour + i, sol.fTour + j + 1);
                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_oropt2(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN - 1; i++) {
            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= i + 1) continue;

                if (sol.evaluateOrOpt(i, i + 1, k)) {
                    int u = sol.fTour[i];
                    int v = sol.fTour[i + 1];

                    if (k > i + 1) {
                        for (int m = i; m <= k - 2; m++)
                            sol.fTour[m] = sol.fTour[m + 2];
                        sol.fTour[k - 1] = u;
                        sol.fTour[k]     = v;
                    } else {
                        for (int m = i + 1; m >= k + 3; m--)
                            sol.fTour[m] = sol.fTour[m - 2];
                        sol.fTour[k + 1] = u;
                        sol.fTour[k + 2] = v;
                    }

                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}

void neighborhood_oropt3(Solution& sol) {
    bool improved = true;

    while (improved) {
        improved = false;

        for (int i = 1; i < sol.fN - 2; i++) {
            for (int k = 0; k < sol.fN; k++) {
                if (k >= i && k <= i + 2) continue;

                if (sol.evaluateOrOpt(i, i + 2, k)) {
                    int u = sol.fTour[i];
                    int v = sol.fTour[i + 1];
                    int w = sol.fTour[i + 2];

                    if (k > i + 2) {
                        for (int m = i; m <= k - 3; m++)
                            sol.fTour[m] = sol.fTour[m + 3];
                        sol.fTour[k - 2] = u;
                        sol.fTour[k - 1] = v;
                        sol.fTour[k]     = w;
                    } else {
                        for (int m = i + 2; m >= k + 4; m--)
                            sol.fTour[m] = sol.fTour[m - 3];
                        sol.fTour[k + 1] = u;
                        sol.fTour[k + 2] = v;
                        sol.fTour[k + 3] = w;
                    }

                    sol.calculateStructures();
                    improved = true;
                }
            }
        }
    }
}
