#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"

using namespace std;


int concat_T(int v, int w, int T1, int T2, Evaluator& eval) {
    return T1 + eval.fEdgeDis[v][w] + T2;
}

int concat_W(int W1, int W2) {
    return W1 + W2;
}

int concat_C(int v, int w, int C1, int C2, int W2, int T1, Evaluator& eval) {
    return C1 + W2 * (T1 + eval.fEdgeDis[v][w]) + C2;
}

int evaluateSwap(
    const Solution& sol,
    int i,
    int j,
    const vector<vector<int>>& T,
    const vector<vector<int>>& C,
    const vector<vector<int>>& W,
    Evaluator& eval
)
{
    if (i > j) swap(i, j);

    int n = sol.fN;
    const int* tour = sol.fTour;

    int Ttotal = 0;
    int Ctotal = 0;
    int Wtotal = 0;

    bool first = true;
    int lastNode = -1;

    auto appendSubseq = [&](int Ti, int Ci, int Wi, int firstNode, int lastNodeSub)
    {
        if (first)
        {
            Ttotal = Ti;
            Ctotal = Ci;
            Wtotal = Wi;
            lastNode = lastNodeSub;
            first = false;
            return;
        }

        Ctotal = concat_C(lastNode, firstNode, Ctotal, Ci, Wi, Ttotal, eval);
        Ttotal = concat_T(lastNode, firstNode, Ttotal, Ti, eval);
        Wtotal = concat_W(Wtotal, Wi);

        lastNode = lastNodeSub;
    };

    // (0, ..., i-1)
    if (i > 0)
        appendSubseq(T[0][i-1], C[0][i-1], W[0][i-1], tour[0], tour[i-1]);

    // (j)
    appendSubseq(T[j][j], C[j][j], W[j][j], tour[j], tour[j]);

    // (i+1, ..., j-1)
    if (i+1 <= j-1)
        appendSubseq(T[i+1][j-1], C[i+1][j-1], W[i+1][j-1], tour[i+1], tour[j-1]);

    // (i)
    appendSubseq(T[i][i], C[i][i], W[i][i], tour[i], tour[i]);

    // (j+1, ..., n-1)
    if (j+1 < n)
        appendSubseq(T[j+1][n-1], C[j+1][n-1], W[j+1][n-1], tour[j+1], tour[n-1]);

    return Ctotal;
}


void PrintAllSubsequences(
    const vector<vector<int>>& T,
    const vector<vector<int>>& C,
    const vector<vector<int>>& W,
    const int* tour,
    int n
)
{
    cout << "\n================ SUBSEQUENCE TABLE ================\n";

    cout << left
         << setw(20) << "Subsequence"
         << setw(10) << "T"
         << setw(10) << "C"
         << setw(10) << "W"
         << "\n";

    cout << string(50, '-') << "\n";

    for (int i = 0; i < n; i++)
    {
        for (int j = i; j < n; j++)
        {
            string seq = "(";
            for (int k = i; k <= j; k++)
            {
                seq += to_string(tour[k]);
                if (k < j) seq += ",";
            }
            seq += ")";

            cout << left
                 << setw(20) << seq
                 << setw(10) << T[i][j]
                 << setw(10) << C[i][j]
                 << setw(10) << W[i][j]
                 << "\n";
        }
    }

    cout << "==================================================\n";
}


void local_search(Solution& sol, Evaluator& eval) {
    Solution s = sol;
    int termination_criterion = 1;

    vector<vector<int>> T(sol.fN, vector<int>(sol.fN));         /* Duration T(σ) to perform the visits sequence σ. (duration of σ) */
    vector<vector<int>> C(sol.fN, vector<int>(sol.fN));         /* Cost C(σ) to perform the sequence, when starting at time 0. (latency cost of σ) */
    vector<vector<int>> W(sol.fN, vector<int>(sol.fN));         /* Delay cost W(σ), related to a one time unit delay in the starting time. (number of customers of σ) */

    for (int i = 0; i < sol.fN; i++)
    {
        int vi = sol.fTour[i];

        T[i][i] = 0;
        C[i][i] = 0;
        W[i][i] = (vi != 0);

        for (int j = i + 1; j < sol.fN; j++)
        {
            int prev = sol.fTour[j-1];
            int curr = sol.fTour[j];

            T[i][j] = T[i][j-1] + eval.fEdgeDis[prev][curr];
            C[i][j] = C[i][j-1] + T[i][j];
            W[i][j] = W[i][j-1] + 1;

        }
    }

    // PrintAllSubsequences(T, C, W, sol.fTour, sol.fN);


    while (termination_criterion--) {
        // Generation of candidate neighbors
        int i, j;
        for (i = 1; i < sol.fN; ++i) {
            for (j = 1; j < sol.fN; ++j) {
                if (i == j) continue;
                int neighborEvaluationValue = evaluateSwap(sol, i, j, T, C, W, eval);

                // Evaluate neighbor by swapping cities i and j
                if (sol.fEvaluationValue > neighborEvaluationValue) {
                    // Make changes in solution
                    swap(s.fTour[i], s.fTour[j]);
                    eval.DoIt(s);
                    sol = s;
                    // cout << "Improved to " << sol.fEvaluationValue << " by swapping " << i << " and " << j << "\n";
                }
            }
        }
    }
    
}

bool parse_route_string(const string& s, Solution& sol) {
    vector<int> vals;
    string token;
    stringstream ss(s);

    while (getline(ss, token, ',')) {
        if (token.empty()) continue;
        vals.push_back(stoi(token));
    }

    if ((int)vals.size() != sol.fN) {
        cerr << "Route size mismatch\n";
        return false;
    }

    vector<bool> used(sol.fN, false);
    for (int i = 0; i < sol.fN; i++) {
        int v = vals[i];
        if (v < 0 || v >= sol.fN || used[v]) {
            cerr << "Invalid route value\n";
            return false;
        }
        sol.fTour[i] = v;
        used[v] = true;
    }

    return true;
}


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./local_search <instance.tsp>\n";
        cerr << "  ./local_search <instance.tsp> --route 0,3,2,5,...\n";
        return 1;
    }

    string instanceFile = argv[1];

    string routeArg = "";

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--route" && i + 1 < argc) {
            routeArg = argv[++i];
        }
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos) {
        filepath = "instances/" + instanceFile;
    }

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    Solution sol;
    sol.Define(eval.Ncity);


    if (!routeArg.empty()) {
        if (!parse_route_string(routeArg, sol)) {
            return 1;
        }
    }
    else {
        for (int i = 0; i < sol.fN; ++i)
            sol.fTour[i] = i;
    }

    eval.DoIt(sol);

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();

    local_search(sol, eval);

    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << sol.fN << "\n";
    cout << "COST " << sol.fEvaluationValue << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < sol.fN; i++) {
        cout << sol.fTour[i] << ",\n"[i == sol.fN - 1];
    }

    return 0;
}
