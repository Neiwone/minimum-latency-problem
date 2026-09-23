#include <bits/stdc++.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* H8: DBMEA-lite (Tuu-Szabo, Foldesi & Koczy, 2020). Per generation:
   bacterial mutation, gene transfer between halves, then RVND. */

struct Individual {
    vector<int> tour;
    int cost;
};

int full_route_cost(const vector<int>& tour, int** dist) {
    int n = (int)tour.size();
    int t = 0, total = 0;
    for (int i = 1; i < n; i++) {
        t += dist[tour[i - 1]][tour[i]];
        total += t;
    }
    return total;
}

void bacterial_mutation(Individual& ind, int** dist, int n, int nClones, int segLen, mt19937& gen) {
    for (int start = 1; start < n; start += segLen) {
        int end = min(start + segLen, n);
        if (end - start < 2) break;

        vector<int> bestSeg(ind.tour.begin() + start, ind.tour.begin() + end);
        int bestCost = ind.cost;

        for (int c = 0; c < nClones; c++) {
            vector<int> candidate = ind.tour;
            if (c == 0) {
                reverse(candidate.begin() + start, candidate.begin() + end);
            } else {
                shuffle(candidate.begin() + start, candidate.begin() + end, gen);
            }
            int cost = full_route_cost(candidate, dist);
            if (cost < bestCost) {
                bestCost = cost;
                bestSeg.assign(candidate.begin() + start, candidate.begin() + end);
            }
        }

        copy(bestSeg.begin(), bestSeg.end(), ind.tour.begin() + start);
        ind.cost = bestCost;
    }
}

void gene_transfer(vector<Individual>& pop, int** dist, int n, int nTransfers, int transferLen, mt19937& gen) {
    sort(pop.begin(), pop.end(), [](const Individual& a, const Individual& b) {
        return a.cost < b.cost;
    });

    int half = max(1, (int)pop.size() / 2);
    uniform_int_distribution<int> superiorDist(0, half - 1);
    uniform_int_distribution<int> inferiorDist(half, (int)pop.size() - 1);

    if ((int)pop.size() - half < 1) return; // population too small to split

    int actualTransferLen = min(transferLen, n - 2);
    if (actualTransferLen < 1) return;

    for (int t = 0; t < nTransfers; t++) {
        int sIdx = superiorDist(gen);
        int iIdx = inferiorDist(gen);
        const vector<int>& donor = pop[sIdx].tour;

        uniform_int_distribution<int> segPosDist(1, n - actualTransferLen - 1);
        int segStart = segPosDist(gen);
        vector<int> segment(donor.begin() + segStart, donor.begin() + segStart + actualTransferLen);

        vector<bool> inSegment(n, false);
        for (int c : segment) inSegment[c] = true;

        vector<int> filtered;
        filtered.reserve(n);
        for (int c : pop[iIdx].tour)
            if (!inSegment[c]) filtered.push_back(c);

        uniform_int_distribution<int> insDist(1, (int)filtered.size());
        int insPos = max(1, insDist(gen));

        vector<int> newTour(filtered.begin(), filtered.begin() + insPos);
        newTour.insert(newTour.end(), segment.begin(), segment.end());
        newTour.insert(newTour.end(), filtered.begin() + insPos, filtered.end());

        pop[iIdx].tour = newTour;
        pop[iIdx].cost = full_route_cost(newTour, dist);
    }
}

void dbmea(Solution& bestSol, Evaluator& eval, int popSize, int generations,
           int nClones, int segLen, int nTransfers, int transferLen,
           int memeticTopK, mt19937& gen) {
    int n = eval.Ncity;
    int** dist = eval.fEdgeDis;

    vector<double> R;
    for (double r = 0.0; r <= 0.25; r += 0.01) R.push_back(r);
    uniform_int_distribution<int> rDist(0, (int)R.size() - 1);

    vector<Individual> pop(popSize);
    for (auto& ind : pop) {
        Solution s;
        construction(s, eval, R[rDist(gen)], gen);
        ind.tour.assign(s.fTour, s.fTour + n);
        ind.cost = s.fEvaluationValue;
    }

    int bestCost = INT_MAX;
    vector<int> bestTour;
    for (const auto& ind : pop)
        if (ind.cost < bestCost) { bestCost = ind.cost; bestTour = ind.tour; }

    for (int g = 0; g < generations; g++) {
        for (auto& ind : pop)
            bacterial_mutation(ind, dist, n, nClones, segLen, gen);

        gene_transfer(pop, dist, n, nTransfers, transferLen, gen);

        sort(pop.begin(), pop.end(), [](const Individual& a, const Individual& b) {
            return a.cost < b.cost;
        });

        /* memeticTopK < popSize stalls the population after one generation:
           an unpolished individual never catches an RVND'd one. */
        int topK = min(memeticTopK, (int)pop.size());
        for (int i = 0; i < topK; i++) {
            Solution s;
            s.Define(n);
            s.fDist = dist;
            for (int k = 0; k < n; k++) s.fTour[k] = pop[i].tour[k];
            s.calculateStructures();

            RVND(s, gen);

            pop[i].tour.assign(s.fTour, s.fTour + n);
            pop[i].cost = s.fEvaluationValue;
        }

        for (const auto& ind : pop)
            if (ind.cost < bestCost) { bestCost = ind.cost; bestTour = ind.tour; }
    }

    bestSol.Define(n);
    bestSol.fDist = dist;
    for (int i = 0; i < n; i++) bestSol.fTour[i] = bestTour[i];
    bestSol.calculateStructures();
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./dbmea <instance.tsp> [--pop-size 20] [--generations 50]\n";
        cerr << "    [--n-clones auto] [--seg-len auto] [--n-transfers auto]\n";
        cerr << "    [--transfer-len auto] [--memetic-top-k auto] [--seed N]\n";
        return 1;
    }

    // Defaults match Tuu-Szabo, Foldesi & Koczy (2020) IJCIS 13(1):781-793:
    // N_ind=100, N_clones=n/15, I_seg=n/20, N_inf=40, I_transfer=n/20.
    string instanceFile = argv[1];
    int popSize = 100;
    int generations = 50;
    int nClones = -1;     // auto: max(5, n/15)
    int segLen = -1;      // auto: max(3, n/20)
    int nTransfers = 40;  // paper's N_inf -- fixed, not tied to popSize
    int transferLen = -1; // auto: max(3, n/20)
    int memeticTopK = -1; // auto: popSize (RVND on everyone -- see note above)
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--pop-size" && i + 1 < argc) popSize = stoi(argv[++i]);
        else if (a == "--generations" && i + 1 < argc) generations = stoi(argv[++i]);
        else if (a == "--n-clones" && i + 1 < argc) nClones = stoi(argv[++i]);
        else if (a == "--seg-len" && i + 1 < argc) segLen = stoi(argv[++i]);
        else if (a == "--n-transfers" && i + 1 < argc) nTransfers = stoi(argv[++i]);
        else if (a == "--transfer-len" && i + 1 < argc) transferLen = stoi(argv[++i]);
        else if (a == "--memetic-top-k" && i + 1 < argc) memeticTopK = stoi(argv[++i]);
        else if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
    }

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());
    int n = eval.Ncity;

    if (nClones < 0) nClones = max(5, n / 15);
    if (segLen < 0) segLen = max(3, n / 20);
    if (nTransfers < 0) nTransfers = popSize;
    if (transferLen < 0) transferLen = max(3, n / 20);
    if (memeticTopK < 0) memeticTopK = popSize;

    Solution bestSol;
    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    dbmea(bestSol, eval, popSize, generations, nClones, segLen, nTransfers,
          transferLen, memeticTopK, gen);

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "POP_SIZE " << popSize << "\n";
    cout << "GENERATIONS " << generations << "\n";
    cout << "N_CLONES " << nClones << "\n";
    cout << "SEG_LEN " << segLen << "\n";
    cout << "N_TRANSFERS " << nTransfers << "\n";
    cout << "TRANSFER_LEN " << transferLen << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
