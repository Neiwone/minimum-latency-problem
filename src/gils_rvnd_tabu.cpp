#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* GILS-RVND with a short tabu list inside RVND, so a neighborhood that just
   fired is not immediately reused. Per restart: construction, then ILS. */

void perturb(Solution& sol, mt19937& gen) {
    int n = sol.fN;
    if (n < 8) return;

    uniform_int_distribution<int> dist(1, n - 1);

    int p1, p2, p3;
    do {
        int a = dist(gen), b = dist(gen), c = dist(gen);
        if (a > b) swap(a, b);
        if (b > c) swap(b, c);
        if (a > b) swap(a, b);
        p1 = a; p2 = b; p3 = c;
    } while (p1 == p2 || p2 == p3);

    int* old = new int[n];
    memcpy(old, sol.fTour, n * sizeof(int));

    uniform_int_distribution<int> pdist(0, 4);
    int perm = pdist(gen);

    int seg[3][2] = {{p1, p2}, {p2, p3}, {p3, n}};
    int order[5][3] = {{0,2,1}, {1,0,2}, {1,2,0}, {2,0,1}, {2,1,0}};

    int pos = 0;
    for (int i = 0; i < p1; i++) sol.fTour[pos++] = old[i];
    for (int s = 0; s < 3; s++) {
        int idx = order[perm][s];
        for (int i = seg[idx][0]; i < seg[idx][1]; i++)
            sol.fTour[pos++] = old[i];
    }

    delete[] old;
    sol.calculateStructures();
}

struct StepTimings {
    double construction_ms = 0;
    double rvnd_ms = 0;
    double total_ms = 0;
};

void gils_rvnd_tabu(Solution& bestSol, Evaluator& eval,
                    int I_max, int I_ILS, int rvndTenure,
                    const vector<double>& R, bool verbose = false,
                    StepTimings* timings = nullptr, long seed = -1) {
    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());
    using Clock = chrono::high_resolution_clock;

    Cost fStar = LLONG_MAX;
    int bestIter = -1;
    double total_construction_ms = 0, total_rvnd_ms = 0;

    for (int i = 0; i < I_max; i++) {
        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        auto tc0 = Clock::now();
        Solution s;
        construction(s, eval, alpha, gen);
        auto tc1 = Clock::now();
        total_construction_ms += chrono::duration<double, milli>(tc1 - tc0).count();

        Solution sPrime(s);
        int iterILS = 0;
        while (iterILS <= I_ILS) {
            // RVND
            auto tr0 = Clock::now();
            RVND_Tabu(s, gen, rvndTenure);
            auto tr1 = Clock::now();
            total_rvnd_ms += chrono::duration<double, milli>(tr1 - tr0).count();

            if (s.fEvaluationValue < sPrime.fEvaluationValue) {
                sPrime = s;
                iterILS = 0;
            }

            s = sPrime;
            perturb(s, gen);
            iterILS++;
        }

        if (verbose) {
            cerr << "  iter " << i << ": cost=" << sPrime.fEvaluationValue << "\n";
        }

        if (sPrime.fEvaluationValue < fStar) {
            bestSol = sPrime;
            fStar = sPrime.fEvaluationValue;
            bestIter = i;
        }
    }

    if (timings) {
        timings->construction_ms = total_construction_ms;
        timings->rvnd_ms = total_rvnd_ms;
    }

    if (verbose) {
        cerr << "best at iter " << bestIter << " cost=" << fStar << "\n";
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./gils_rvnd_tabu <instance.tsp> [--imax 10] [--iils 50] "
            "[--tenure 7] [--seed N] [-v]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int I_max = 10;
    int I_ILS = -1;        // default: min(n, 100)
    int rvndTenure = -1;   // default: sqrt(n)
    bool verbose = false;
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--imax" && i + 1 < argc)
            I_max = stoi(argv[++i]);
        else if (a == "--iils" && i + 1 < argc)
            I_ILS = stoi(argv[++i]);
        else if (a == "--tenure" && i + 1 < argc)
            rvndTenure = stoi(argv[++i]);
        else if (a == "--seed" && i + 1 < argc)
            seed = stol(argv[++i]);
        else if (a == "--verbose" || a == "-v")
            verbose = true;
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    int n = eval.Ncity;
    if (I_ILS < 0)    I_ILS = min(n, 100);
    if (rvndTenure < 0) rvndTenure = max(1, (int)sqrt(n));

    vector<double> R;
    for (double r = 0.00; r <= 0.25; r += 0.01)
        R.push_back(r);

    Solution bestSol;
    StepTimings timings;

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    gils_rvnd_tabu(bestSol, eval, I_max, I_ILS, rvndTenure, R, verbose, &timings, seed);

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();
    timings.total_ms = runtime_ms;

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "IILS " << I_ILS << "\n";
    cout << "TENURE " << rvndTenure << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "CONSTRUCTION_MS " << fixed << setprecision(3) << timings.construction_ms << "\n";
    cout << "RVND_MS " << fixed << setprecision(3) << timings.rvnd_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
