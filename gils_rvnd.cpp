#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

void perturb(Solution& sol, mt19937& gen) {
    int n = sol.fN;
    if (n < 8) return;

    vector<int> cuts;
    uniform_int_distribution<int> dist(1, n - 2);

    while ((int)cuts.size() < 3) {
        int c = dist(gen);
        bool dup = false;
        for (int x : cuts) if (x == c) { dup = true; break; }
        if (!dup) cuts.push_back(c);
    }
    sort(cuts.begin(), cuts.end());

    int p1 = cuts[0], p2 = cuts[1], p3 = cuts[2];

    // Segments: [0..p1-1], [p1..p2-1], [p2..p3-1], [p3..n-1]
    // Double-bridge: reconnect as seg1 + seg3 + seg2 + seg4
    vector<int> newTour;
    newTour.reserve(n);

    for (int i = 0;  i < p1; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p2; i < p3; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p1; i < p2; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p3; i < n;  i++) newTour.push_back(sol.fTour[i]);

    for (int i = 0; i < n; i++)
        sol.fTour[i] = newTour[i];

    sol.calculateStructures();
}

void gils_rvnd(Solution& bestSol, Evaluator& eval,
               int I_max, int I_ILS, const vector<double>& R) {
    random_device rd;
    mt19937 gen(rd());

    int fStar = INT_MAX;

    for (int i = 0; i < I_max; i++) {
        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        Solution s;
        construction(s, eval, alpha, gen);

        Solution sPrime(s);

        int iterILS = 0;

        while (iterILS < I_ILS) {
            RVND(s, gen);

            if (s.fEvaluationValue < sPrime.fEvaluationValue) {
                sPrime = s;
                iterILS = 0;
            }

            s = sPrime;
            perturb(s, gen);

            iterILS++;
        }

        if (sPrime.fEvaluationValue < fStar) {
            bestSol = sPrime;
            fStar = sPrime.fEvaluationValue;
        }
    }
}


int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./gils_rvnd <instance.tsp> [--imax 10] [--iils 50]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int I_max = 10;
    int I_ILS = 100;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--imax" && i + 1 < argc) {
            I_max = stoi(argv[++i]);
        }
        else if (a == "--iils" && i + 1 < argc) {
            I_ILS = min(100, stoi(argv[++i]));
        }
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos) {
        filepath = "instances/" + instanceFile;
    }

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    vector<double> R;
    for (double r = 0.0; r <= 0.25; r += 0.01)
        R.push_back(r);

    Solution bestSol;

    using Clock = chrono::high_resolution_clock;

    auto t0 = Clock::now();

    gils_rvnd(bestSol, eval, I_max, I_ILS, R);

    auto t1 = Clock::now();

    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "IILS " << I_ILS << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++) {
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];
    }

    return 0;
}
