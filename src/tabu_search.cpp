#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"

using namespace std;

struct TabuMove {
    int type;       // 0=swap, 1=2opt, 2=reinsertion, 3=oropt2, 4=oropt3
    int i, j, k;
    bool reversed;
    int cost;
};

static void applyTabuMove(Solution& sol, const TabuMove& move) {
    switch (move.type) {
        case 0: // swap
            swap(sol.fTour[move.i], sol.fTour[move.j]);
            break;

        case 1: // 2-opt
            reverse(sol.fTour + move.i, sol.fTour + move.j + 1);
            break;

        case 2: { // reinsertion
            int node = sol.fTour[move.i];
            if (move.i < move.j) {
                for (int m = move.i; m < move.j; m++)
                    sol.fTour[m] = sol.fTour[m + 1];
                sol.fTour[move.j] = node;
            } else {
                for (int m = move.i; m > move.j + 1; m--)
                    sol.fTour[m] = sol.fTour[m - 1];
                sol.fTour[move.j + 1] = node;
            }
            break;
        }

        case 3: { // or-opt2
            int u, v;
            if (move.reversed) {
                u = sol.fTour[move.i + 1];
                v = sol.fTour[move.i];
            } else {
                u = sol.fTour[move.i];
                v = sol.fTour[move.i + 1];
            }

            if (move.k > move.i + 1) {
                for (int m = move.i; m <= move.k - 2; m++)
                    sol.fTour[m] = sol.fTour[m + 2];
                sol.fTour[move.k - 1] = u;
                sol.fTour[move.k]     = v;
            } else {
                for (int m = move.i + 1; m >= move.k + 3; m--)
                    sol.fTour[m] = sol.fTour[m - 2];
                sol.fTour[move.k + 1] = u;
                sol.fTour[move.k + 2] = v;
            }
            break;
        }

        case 4: { // or-opt3
            int u, v, w;
            if (move.reversed) {
                u = sol.fTour[move.i + 2];
                v = sol.fTour[move.i + 1];
                w = sol.fTour[move.i];
            } else {
                u = sol.fTour[move.i];
                v = sol.fTour[move.i + 1];
                w = sol.fTour[move.i + 2];
            }

            if (move.k > move.i + 2) {
                for (int m = move.i; m <= move.k - 3; m++)
                    sol.fTour[m] = sol.fTour[m + 3];
                sol.fTour[move.k - 2] = u;
                sol.fTour[move.k - 1] = v;
                sol.fTour[move.k]     = w;
            } else {
                for (int m = move.i + 2; m >= move.k + 4; m--)
                    sol.fTour[m] = sol.fTour[m - 3];
                sol.fTour[move.k + 1] = u;
                sol.fTour[move.k + 2] = v;
                sol.fTour[move.k + 3] = w;
            }
            break;
        }
    }
}

void tabu_search(Solution& bestSol, Evaluator& eval, int I_max, int maxIter,
                 int tenure, const vector<double>& R, bool verbose) {
    random_device rd;
    mt19937 gen(rd());
    using Clock = chrono::high_resolution_clock;

    int n = eval.Ncity;
    int bestGlobalCost = INT_MAX;

    vector<vector<int>> tabuMatrix(n, vector<int>(n, -tenure - 1));

    for (int restart = 0; restart < I_max; restart++) {
        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        Solution s;
        construction(s, eval, alpha, gen);

        Solution bestLocal(s);

        for (auto& row : tabuMatrix)
            fill(row.begin(), row.end(), -tenure - 1);

        auto t0 = Clock::now();

        for (int iter = 0; iter < maxIter; iter++) {
            TabuMove bestMove = {-1, -1, -1, -1, false, INT_MAX};
            int currentCost = s.fEvaluationValue;
            bool aspiration = (currentCost == bestGlobalCost);

            // swap
            for (int i = 1; i < n; i++) {
                if (bestMove.type != -1) break;
                for (int j = i + 1; j < n; j++) {
                    bool isTabu = (tabuMatrix[s.fTour[i]][j] > iter - tenure) ||
                                  (tabuMatrix[s.fTour[j]][i] > iter - tenure);
                    if (isTabu && !aspiration) continue;
                    if (s.evaluateSwap(i, j)) {
                        bestMove = {0, i, j, -1, false, INT_MAX};
                        break;
                    }
                }
            }

            // reinsertion
            if (bestMove.type == -1) {
                for (int i = 1; i < n; i++) {
                    if (bestMove.type != -1) break;
                    for (int j = 0; j < n; j++) {
                        if (i == j) continue;

                        int targetPos = (i < j) ? j : j + 1;
                        bool isTabu = (tabuMatrix[s.fTour[i]][targetPos] > iter - tenure);
                        if (isTabu && !aspiration) continue;
                        if (s.evaluateReinsertion(i, j)) {
                            bestMove = {2, i, j, -1, false, INT_MAX};
                            break;
                        }
                    }
                }
            }

            // 2opt
            if (bestMove.type == -1) {
                for (int i = 1; i < n; i++) {
                    if (bestMove.type != -1) break;
                    for (int j = i + 1; j < n; j++) {
                        bool isTabu = (tabuMatrix[s.fTour[j]][i] > iter - tenure) ||
                                      (tabuMatrix[s.fTour[i]][j] > iter - tenure);
                        if (isTabu && !aspiration) continue;
                        if (s.evaluate2Opt(i, j)) {
                            bestMove = {1, i, j, -1, false, INT_MAX};
                            break;
                        }
                    }
                }
            }

            // oropt2
            if (bestMove.type == -1) {
                for (int i = 1; i < n - 1; i++) {
                    if (bestMove.type != -1) break;
                    for (int k = 0; k < n; k++) {
                        if (k >= i && k <= i + 1) continue;

                        int targetPos = (k > i + 1) ? k - 1 : k + 1;
                        bool isTabu = (tabuMatrix[s.fTour[i]][targetPos] > iter - tenure);
                        if (isTabu && !aspiration) continue;
                        if (s.evaluateOrOpt(i, i + 1, k)) {
                            bestMove = {3, i, -1, k, false, INT_MAX};
                            break;
                        }
                    }
                }
            }

            // oropt3
            if (bestMove.type == -1) {
                for (int i = 1; i < n - 2; i++) {
                    if (bestMove.type != -1) break;
                    for (int k = 0; k < n; k++) {
                        if (k >= i && k <= i + 2) continue;

                        int targetPos = (k > i + 2) ? k - 2 : k + 1;
                        bool isTabu = (tabuMatrix[s.fTour[i]][targetPos] > iter - tenure);
                        if (isTabu && !aspiration) continue;
                        if (s.evaluateOrOpt(i, i + 2, k)) {
                            bestMove = {4, i, -1, k, false, INT_MAX};
                            break;
                        }
                    }
                }
            }

            if (bestMove.type == -1) break;

            switch (bestMove.type) {
                case 0: { // swap
                    int ni = s.fTour[bestMove.i], nj = s.fTour[bestMove.j];
                    tabuMatrix[ni][bestMove.i] = iter;
                    tabuMatrix[nj][bestMove.j] = iter;
                    break;
                }
                case 1: { // 2-opt
                    tabuMatrix[s.fTour[bestMove.i]][bestMove.i] = iter;
                    tabuMatrix[s.fTour[bestMove.j]][bestMove.j] = iter;
                    break;
                }
                case 2: { // reinsertion
                    int node = s.fTour[bestMove.i];
                    tabuMatrix[node][bestMove.i] = iter;
                    break;
                }
                case 3: { // or-opt2
                    tabuMatrix[s.fTour[bestMove.i]][bestMove.i] = iter;
                    tabuMatrix[s.fTour[bestMove.i + 1]][bestMove.i + 1] = iter;
                    break;
                }
                case 4: { // or-opt3
                    tabuMatrix[s.fTour[bestMove.i]][bestMove.i] = iter;
                    tabuMatrix[s.fTour[bestMove.i + 1]][bestMove.i + 1] = iter;
                    tabuMatrix[s.fTour[bestMove.i + 2]][bestMove.i + 2] = iter;
                    break;
                }
            }

            applyTabuMove(s, bestMove);

            s.calculateStructures();

            if (s.fEvaluationValue < bestLocal.fEvaluationValue) {
                bestLocal = s;
            }
        }

        auto t1 = Clock::now();
        double ms = chrono::duration<double, milli>(t1 - t0).count();

        if (verbose) {
            cerr << "  restart " << restart << ": cost=" << bestLocal.fEvaluationValue
                 << "  time=" << fixed << setprecision(1) << ms << "ms\n";
        }

        if (bestLocal.fEvaluationValue < bestGlobalCost) {
            bestGlobalCost = bestLocal.fEvaluationValue;
            bestSol = bestLocal;
        }
    }
}


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./tabu_search <instance.tsp> [--imax 10] [--iter 10] [--tenure sqrt(n)]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int I_max = 10;     // default aligned with grasp-style 10 iterations
    int maxIter = -1;   // default: 10
    int tenure = -1;    // default: sqrt(n)
    bool verbose = false;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--imax" && i + 1 < argc)
            I_max = stoi(argv[++i]);
        else if (a == "--iter" && i + 1 < argc)
            maxIter = stoi(argv[++i]);
        else if (a == "--tenure" && i + 1 < argc)
            tenure = stoi(argv[++i]);
        else if (a == "--verbose" || a == "-v")
            verbose = true;
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    int n = eval.Ncity;
    if (maxIter < 0) maxIter = 10;
    if (tenure < 0)  tenure = max(1, (int)sqrt(n));

    vector<double> R;
    for (double r = 0.00; r <= 0.25; r += 0.01)
        R.push_back(r);

    Solution bestSol;

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    tabu_search(bestSol, eval, I_max, maxIter, tenure, R, verbose);

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "ITER " << maxIter << "\n";
    cout << "TENURE " << tenure << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
