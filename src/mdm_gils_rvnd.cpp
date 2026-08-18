#include <bits/stdc++.h>
#include <cstdio>
#include <unistd.h>
#include "solution.h"
#include "evaluator.h"
#include "construction.h"
#include "rvnd.h"

using namespace std;

/* H13: MDM-GILS-RVND (Santana, Plastino & Rosseti, "Improving a
   State-of-the-Art Heuristic for the Minimum Latency Problem with Data
   Mining", arXiv:1908.10705) -- see docs/experiments/h13-mdm-gils-rvnd.md.

   Unlike our own GRASP-AM/GILS-AM-RVND (src/grasp_am.cpp,
   src/gils_am_rvnd.cpp -- which bias construction by INDIVIDUAL edge
   frequency across the elite pool, tested in this session as ties
   quality / wins speed, never wins quality), the paper mines MAXIMAL
   FREQUENT CONSECUTIVE-ARC SEGMENTS (whole sub-paths, not single edges)
   and splices them into new constructions as atomic units. Reported
   result: quality *and* speed both improve, growing with n (up to
   32.78% faster and 19/20 best-solution wins at n=1000).

   Mining uses the REAL FPMax* algorithm (not a hand-rolled proxy): each
   elite tour is a "transaction" of arcs, and scripts/fpmax_mine.py
   (mlxtend.frequent_patterns.fpmax) computes genuine maximal frequent
   itemsets, invoked via a subprocess since mining only happens a handful
   of times per run (whenever the elite set changes during phase 2) --
   negligible overhead against total runtime. A first version of this
   file used a hand-rolled proxy (individually-frequent arcs chained into
   runs) instead; that is NOT equivalent to true itemset mining, because
   itemset support is monotonically non-increasing with itemset size
   (Apriori/downward-closure) -- a chain of individually-frequent arcs is
   not guaranteed to be JOINTLY frequent as a set, which the proxy
   silently assumed. Consecutive Arc Lists are reconstructed from each
   mined maximal itemset by finding, within each elite tour, the maximal
   runs of consecutive arcs that are all members of that itemset.
   Candidate segments are deduplicated by node sequence and capped at
   maxPatterns (longest first).

   Two-phase adaptive mining (the "M" in MDM, vs. single-shot DM):
   first half of I_max restarts run plain GILS-RVND (build the elite
   pool); from the second half on, patterns are re-mined every time the
   elite set changes, and construction is guided by them. */

void double_bridge_once(Solution& sol, mt19937& gen) {
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

    vector<int> newTour;
    newTour.reserve(n);
    for (int i = 0;  i < p1; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p2; i < p3; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p1; i < p2; i++) newTour.push_back(sol.fTour[i]);
    for (int i = p3; i < n;  i++) newTour.push_back(sol.fTour[i]);
    for (int i = 0; i < n; i++) sol.fTour[i] = newTour[i];
}

void perturb(Solution& sol, mt19937& gen) {
    double_bridge_once(sol, gen);
    sol.calculateStructures();
}

struct EliteSet {
    vector<Solution> sols;
    int maxSize;
    bool dirty = false; // true if changed since last mining

    explicit EliteSet(int maxSize_) : maxSize(maxSize_) {}

    void add(const Solution& s) {
        for (const auto& es : sols) {
            if (es.fEvaluationValue != s.fEvaluationValue) continue;
            if (equal(es.fTour, es.fTour + es.fN, s.fTour)) return;
        }
        sols.push_back(s);
        sort(sols.begin(), sols.end(), [](const Solution& a, const Solution& b) {
            return a.fEvaluationValue < b.fEvaluationValue;
        });
        if ((int)sols.size() > maxSize) sols.pop_back();
        dirty = true;
    }
};

struct Segment {
    vector<int> nodes; // consecutive customers, length >= 2
};

static string arc_token(int u, int v) {
    return to_string(u) + "_" + to_string(v);
}

/* Real FPMax* (mlxtend, via scripts/fpmax_mine.py subprocess): writes
   the elite pool as arc-transactions, runs genuine maximal frequent
   itemset mining, reads back the mined itemsets, then reconstructs
   Consecutive Arc Lists by finding, within each elite tour, the maximal
   runs of consecutive arcs that are all members of a given mined
   itemset. See file header for why this replaced the earlier
   individually-frequent-arc-chain proxy. */
vector<Segment> mine_patterns(const EliteSet& elite, double supMin, int maxPatterns) {
    int d = (int)elite.sols.size();
    if (d == 0) return {};

    string tag = to_string(getpid());
    string inPath = "/tmp/mdm_mine_" + tag + "_in.txt";
    string outPath = "/tmp/mdm_mine_" + tag + "_out.txt";

    {
        ofstream out(inPath);
        for (const auto& s : elite.sols) {
            for (int i = 0; i + 1 < s.fN; i++) {
                if (i > 0) out << ' ';
                out << arc_token(s.fTour[i], s.fTour[i + 1]);
            }
            out << '\n';
        }
    }

    string cmd = "uv run --with mlxtend --with pandas python3 scripts/fpmax_mine.py "
                 + inPath + " " + to_string(supMin) + " " + outPath + " >/dev/null 2>&1";
    int rc = system(cmd.c_str());
    (void)rc; // best-effort: an empty/missing output file below is treated as "no patterns"

    vector<vector<string>> minedItemsets;
    {
        ifstream in(outPath);
        string line;
        while (getline(in, line)) {
            vector<string> tokens;
            stringstream ss(line);
            string tok;
            while (ss >> tok) tokens.push_back(tok);
            if (!tokens.empty()) minedItemsets.push_back(tokens);
        }
    }
    remove(inPath.c_str());
    remove(outPath.c_str());

    set<vector<int>> seen;
    vector<Segment> candidates;

    for (const auto& itemset : minedItemsets) {
        unordered_set<string> arcSet(itemset.begin(), itemset.end());

        for (const auto& s : elite.sols) {
            int n = s.fN;
            int i = 0;
            while (i < n - 1) {
                if (!arcSet.count(arc_token(s.fTour[i], s.fTour[i + 1]))) { i++; continue; }
                int j = i;
                while (j + 1 < n - 1 && arcSet.count(arc_token(s.fTour[j + 1], s.fTour[j + 2]))) j++;
                vector<int> nodes(s.fTour + i, s.fTour + j + 2);
                if (seen.insert(nodes).second)
                    candidates.push_back({nodes});
                i = j + 1;
            }
        }
    }

    sort(candidates.begin(), candidates.end(), [](const Segment& a, const Segment& b) {
        return a.nodes.size() > b.nodes.size();
    });
    if ((int)candidates.size() > maxPatterns)
        candidates.resize(maxPatterns);

    return candidates;
}

/* Algorithm 5 (HybridConstructiveProc): same semi-greedy RCL/alpha
   mechanism as construction(), but when the selected candidate is the
   first node of a still-fully-unvisited mined segment, the whole
   segment is spliced in as one atomic step instead of just that node. */
void construction_mdm(Solution& sol, Evaluator& eval, double alpha,
                       const unordered_map<int, Segment>& segStarts, mt19937& gen) {
    int n = eval.Ncity;
    double alphaClamped = max(0.0, min(alpha, 1.0));

    vector<bool> visited(n, false);
    vector<int> route;
    route.reserve(n);
    route.push_back(0);
    visited[0] = true;
    int current = 0;

    auto segmentViable = [&](const Segment& seg) {
        for (int node : seg.nodes) if (visited[node]) return false;
        return true;
    };

    while ((int)route.size() < n) {
        vector<int> candidates;
        for (int v = 1; v < n; v++)
            if (!visited[v]) candidates.push_back(v);

        vector<pair<int, int>> scored; // (node, distance)
        scored.reserve(candidates.size());
        int minCost = INT_MAX, maxCost = INT_MIN;
        for (int v : candidates) {
            int d = eval.fEdgeDis[current][v];
            scored.push_back({v, d});
            minCost = min(minCost, d);
            maxCost = max(maxCost, d);
        }

        int threshold = minCost + (int)llround(alphaClamped * (maxCost - minCost));
        vector<int> rcl;
        for (const auto& [v, d] : scored)
            if (d <= threshold) rcl.push_back(v);
        if (rcl.empty()) rcl.push_back(scored.front().first);

        uniform_int_distribution<int> dist(0, (int)rcl.size() - 1);
        int chosen = rcl[dist(gen)];

        auto it = segStarts.find(chosen);
        if (it != segStarts.end() && segmentViable(it->second)) {
            for (int node : it->second.nodes) { route.push_back(node); visited[node] = true; }
            current = it->second.nodes.back();
        } else {
            route.push_back(chosen);
            visited[chosen] = true;
            current = chosen;
        }
    }

    sol.Define(n);
    sol.fDist = eval.fEdgeDis;
    for (int i = 0; i < n; i++) sol.fTour[i] = route[i];
    sol.calculateStructures();
}

void mdm_gils_rvnd(Solution& bestSol, Evaluator& eval, int I_max, int I_ILS,
                    const vector<double>& R, int poolSize, double supMin,
                    int maxPatterns, mt19937& gen) {
    int fStar = INT_MAX;
    EliteSet elite(poolSize);
    unordered_map<int, Segment> segStarts; // empty until phase 2 mines something

    int phase1Iters = max(1, I_max / 2);

    for (int i = 0; i < I_max; i++) {
        bool usePatterns = (i >= phase1Iters) && !segStarts.empty();

        if (i >= phase1Iters && elite.dirty) {
            vector<Segment> segs = mine_patterns(elite, supMin, maxPatterns);
            segStarts.clear();
            for (auto& seg : segs) segStarts[seg.nodes.front()] = seg;
            elite.dirty = false;
            usePatterns = !segStarts.empty();
        }

        uniform_int_distribution<int> rDist(0, (int)R.size() - 1);
        double alpha = R[rDist(gen)];

        Solution s;
        if (usePatterns) construction_mdm(s, eval, alpha, segStarts, gen);
        else construction(s, eval, alpha, gen);

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

        elite.add(sPrime);

        if (sPrime.fEvaluationValue < fStar) {
            bestSol = sPrime;
            fStar = sPrime.fEvaluationValue;
        }
    }
}

int main(int argc, char** argv) {
    if (argc < 2) {
        cerr << "Usage:\n";
        cerr << "  ./mdm_gils_rvnd <instance.tsp> [--imax 10] [--iils 100] [--pool 10]\n";
        cerr << "    [--sup-min 0.70] [--max-patterns 5] [--seed N]\n";
        return 1;
    }

    string instanceFile = argv[1];
    int I_max = 10;
    int I_ILS = 100;
    int poolSize = 10;
    double supMin = 0.70;
    int maxPatterns = 5;
    long seed = -1;

    for (int i = 2; i < argc; i++) {
        string a = argv[i];
        if (a == "--imax" && i + 1 < argc) I_max = stoi(argv[++i]);
        else if (a == "--iils" && i + 1 < argc) I_ILS = stoi(argv[++i]);
        else if (a == "--pool" && i + 1 < argc) poolSize = stoi(argv[++i]);
        else if (a == "--sup-min" && i + 1 < argc) supMin = stod(argv[++i]);
        else if (a == "--max-patterns" && i + 1 < argc) maxPatterns = stoi(argv[++i]);
        else if (a == "--seed" && i + 1 < argc) seed = stol(argv[++i]);
    }

    if (poolSize < 1) poolSize = 1;

    string filepath = instanceFile;
    if (instanceFile.find('/') == string::npos)
        filepath = "instances/" + instanceFile;

    Evaluator eval;
    eval.SetInstance((char*)filepath.c_str());

    vector<double> R;
    for (double r = 0.0; r <= 0.25; r += 0.01) R.push_back(r);

    Solution bestSol;
    mt19937 gen(seed >= 0 ? (unsigned long)seed : random_device{}());

    using Clock = chrono::high_resolution_clock;
    auto t0 = Clock::now();

    mdm_gils_rvnd(bestSol, eval, I_max, I_ILS, R, poolSize, supMin, maxPatterns, gen);

    auto t1 = Clock::now();
    double runtime_ms = chrono::duration<double, milli>(t1 - t0).count();

    cout << "INSTANCE " << instanceFile << "\n";
    cout << "NODES " << bestSol.fN << "\n";
    cout << "COST " << bestSol.fEvaluationValue << "\n";
    cout << "IMAX " << I_max << "\n";
    cout << "IILS " << I_ILS << "\n";
    cout << "POOL " << poolSize << "\n";
    cout << "SUP_MIN " << fixed << setprecision(2) << supMin << "\n";
    cout << "MAX_PATTERNS " << maxPatterns << "\n";
    cout << "TIME_MS " << fixed << setprecision(3) << runtime_ms << "\n";
    cout << "ROUTE ";
    for (int i = 0; i < bestSol.fN; i++)
        cout << bestSol.fTour[i] << ",\n"[i == bestSol.fN - 1];

    return 0;
}
