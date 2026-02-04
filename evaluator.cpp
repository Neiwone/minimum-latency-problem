#ifndef __EVALUATOR__
#include "evaluator.h"
#endif

Evaluator::Evaluator() {
    fEdgeDis = NULL;
    fNearCity = NULL;
    Ncity = 0;
    fNearNumMax = 50;  
}

Evaluator::~Evaluator() {

    for ( int i = 0; i < Ncity; ++i ) 
        delete[] fEdgeDis[ i ];
    delete[] fEdgeDis;

    for ( int i = 0; i < Ncity; ++i ) 
        delete[] fNearCity[ i ];
    delete[] fNearCity;
  
    delete [] x;
    delete [] y;
}

void Evaluator::SetInstance(char filename[]) {

    FILE* fp = fopen(filename, "r");
    if (!fp) {
        printf("Cannot open instance file\n");
        exit(1);
    }

    char word[128], type[128];
    Ncity = 0;

    // ---------- READ HEADER ----------
    while (fscanf(fp, "%s", word) != EOF) {

        if (strcmp(word, "DIMENSION") == 0 || strcmp(word, "DIMENSION:") == 0) {
            if (word[strlen(word)-1] != ':')
                fscanf(fp, "%s", word); // skip ":"
            fscanf(fp, "%d", &Ncity);
        }

        else if (strcmp(word, "EDGE_WEIGHT_TYPE") == 0 || strcmp(word, "EDGE_WEIGHT_TYPE:") == 0) {
            if (word[strlen(word)-1] != ':')
                fscanf(fp, "%s", word);
            fscanf(fp, "%s", type);
        }

        else if (strcmp(word, "NODE_COORD_SECTION") == 0) {
            break;
        }
    }

    if (Ncity <= 0) {
        printf("Invalid DIMENSION\n");
        exit(1);
    }

    // ---------- READ COORDS ----------
    x = new double[Ncity];
    y = new double[Ncity];

    for (int i = 0; i < Ncity; ++i) {
        int id;
        fscanf(fp, "%d %lf %lf", &id, &x[i], &y[i]);
    }

    fclose(fp);

    // ---------- DISTANCE MATRIX ----------
    fEdgeDis = new int*[Ncity];
    for (int i = 0; i < Ncity; ++i)
        fEdgeDis[i] = new int[Ncity];

    if (strcmp(type, "EUC_2D") != 0) {
        printf("Unsupported EDGE_WEIGHT_TYPE: %s\n", type);
        exit(1);
    }

    for (int i = 0; i < Ncity; ++i) {
        for (int j = 0; j < Ncity; ++j) {
            double dx = x[i] - x[j];
            double dy = y[i] - y[j];
            double d = sqrt(dx*dx + dy*dy);
            fEdgeDis[i][j] = (int)(d + 0.5);   // ✅ TSPLIB rounding
        }
    }

    // ---------- NEAREST LIST ----------
    int kmax = std::min(fNearNumMax, Ncity-1);

    fNearCity = new int*[Ncity];
    for (int i = 0; i < Ncity; ++i)
        fNearCity[i] = new int[kmax + 1];

    for (int ci = 0; ci < Ncity; ++ci) {

        std::vector<int> used(Ncity, 0);
        used[ci] = 1;
        fNearCity[ci][0] = ci;

        for (int k = 1; k <= kmax; ++k) {
            int best = -1;
            int bestd = INT_MAX;

            for (int j = 0; j < Ncity; ++j) {
                if (!used[j] && fEdgeDis[ci][j] < bestd) {
                    bestd = fEdgeDis[ci][j];
                    best = j;
                }
            }

            fNearCity[ci][k] = best;
            used[best] = 1;
        }
    }
}


void Evaluator::DoIt(Solution& sol) {

    double walked = 0.0;
    double cost = 0.0;

    for (int i = 0; i < sol.fN - 1; ++i) {
        int u = sol.fTour[i];
        int v = sol.fTour[i + 1];

        walked += fEdgeDis[u][v];
        cost += walked;
    }

    sol.fEvaluationValue = cost;
}


int Evaluator::evaluateSwap(const Solution& sol, int i, int j) {
    // Create a copy of the solution to evaluate the swap
    Solution neighbor;
    neighbor.Define(sol.fN);
    neighbor = sol;

    // Swap cities at positions i and j
    swap(neighbor.fTour[i], neighbor.fTour[j]);

    // Evaluate the new solution
    DoIt(neighbor);

    return neighbor.fEvaluationValue;
}