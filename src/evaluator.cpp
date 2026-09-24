#ifndef __EVALUATOR__
#include "evaluator.h"
#endif

#include <cmath>
#include <climits>
#include <vector>
#include <algorithm>
#include <cstring>
#include <cstdio>
#include <cstdlib>

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

    char word[128], type[128], fmt[128];
    Ncity = 0;
    type[0] = fmt[0] = '\0';
    bool explicitMatrix = false;

    // ---------- READ HEADER ----------
    while (fscanf(fp, "%s", word) != EOF) {

        if (strcmp(word, "DIMENSION") == 0 || strcmp(word, "DIMENSION:") == 0) {
            if (word[strlen(word)-1] != ':')
                fscanf(fp, "%s", word);
            fscanf(fp, "%d", &Ncity);
        }

        else if (strcmp(word, "EDGE_WEIGHT_TYPE") == 0 || strcmp(word, "EDGE_WEIGHT_TYPE:") == 0) {
            if (word[strlen(word)-1] != ':')
                fscanf(fp, "%s", word);
            fscanf(fp, "%s", type);
        }

        else if (strcmp(word, "EDGE_WEIGHT_FORMAT") == 0 || strcmp(word, "EDGE_WEIGHT_FORMAT:") == 0) {
            if (word[strlen(word)-1] != ':')
                fscanf(fp, "%s", word);
            fscanf(fp, "%s", fmt);
        }

        else if (strcmp(word, "NODE_COORD_SECTION") == 0) {
            break;
        }

        else if (strcmp(word, "EDGE_WEIGHT_SECTION") == 0) {
            explicitMatrix = true;
            break;
        }
    }

    if (Ncity <= 0) {
        printf("Invalid DIMENSION\n");
        exit(1);
    }

    x = new double[Ncity];
    y = new double[Ncity];

    fEdgeDis = new int*[Ncity];
    for (int i = 0; i < Ncity; ++i)
        fEdgeDis[i] = new int[Ncity];

    if (explicitMatrix) {
        // ---------- EXPLICIT MATRIX ----------
        for (int i = 0; i < Ncity; ++i) {
            x[i] = y[i] = 0.0;
            for (int j = 0; j < Ncity; ++j) fEdgeDis[i][j] = 0;
        }

        // Each format lists a different triangle; read it then mirror.
        int lo, hi;
        for (int i = 0; i < Ncity; ++i) {
            if      (strcmp(fmt, "FULL_MATRIX")    == 0) { lo = 0;     hi = Ncity - 1; }
            else if (strcmp(fmt, "UPPER_ROW")      == 0) { lo = i + 1; hi = Ncity - 1; }
            else if (strcmp(fmt, "UPPER_DIAG_ROW") == 0) { lo = i;     hi = Ncity - 1; }
            else if (strcmp(fmt, "LOWER_ROW")      == 0) { lo = 0;     hi = i - 1; }
            else if (strcmp(fmt, "LOWER_DIAG_ROW") == 0) { lo = 0;     hi = i; }
            else {
                printf("Unsupported EDGE_WEIGHT_FORMAT: %s\n", fmt);
                exit(1);
            }
            for (int j = lo; j <= hi; ++j) {
                int d;
                if (fscanf(fp, "%d", &d) != 1) {
                    printf("Truncated EDGE_WEIGHT_SECTION at (%d,%d)\n", i, j);
                    exit(1);
                }
                fEdgeDis[i][j] = fEdgeDis[j][i] = d;
            }
        }
    }
    else {
        // ---------- READ COORDS ----------
        for (int i = 0; i < Ncity; ++i) {
            int id;
            fscanf(fp, "%d %lf %lf", &id, &x[i], &y[i]);
        }

        if (strcmp(type, "EUC_2D") == 0) {
            for (int i = 0; i < Ncity; ++i) {
                for (int j = 0; j < Ncity; ++j) {
                    double dx = x[i] - x[j];
                    double dy = y[i] - y[j];
                    fEdgeDis[i][j] = (int)sqrt(dx*dx + dy*dy);
                }
            }
        }
        else if (strcmp(type, "CEIL_2D") == 0) {
            for (int i = 0; i < Ncity; ++i) {
                for (int j = 0; j < Ncity; ++j) {
                    double dx = x[i] - x[j];
                    double dy = y[i] - y[j];
                    fEdgeDis[i][j] = (int)ceil(sqrt(dx*dx + dy*dy));
                }
            }
        }
        else if (strcmp(type, "ATT") == 0) {
            for (int i = 0; i < Ncity; ++i) {
                for (int j = 0; j < Ncity; ++j) {
                    double dx = x[i] - x[j];
                    double dy = y[i] - y[j];
                    double rij = sqrt((dx * dx + dy * dy) / 10.0);
                    int tij = (int)(rij);
                    fEdgeDis[i][j] = (tij < rij) ? tij + 1 : tij;
                }
            }
        }
        else if (strcmp(type, "GEO") == 0) {
            // TSPLIB geographical: DDD.MM coordinates -> radians, great circle.
            const double PI = 3.141592, RRR = 6378.388;
            std::vector<double> lat(Ncity), lon(Ncity);
            for (int i = 0; i < Ncity; ++i) {
                double dg = (int)x[i], mn = x[i] - dg;
                lat[i] = PI * (dg + 5.0 * mn / 3.0) / 180.0;
                dg = (int)y[i]; mn = y[i] - dg;
                lon[i] = PI * (dg + 5.0 * mn / 3.0) / 180.0;
            }
            for (int i = 0; i < Ncity; ++i) {
                for (int j = 0; j < Ncity; ++j) {
                    if (i == j) { fEdgeDis[i][j] = 0; continue; }  // formula would give 1
                    double q1 = cos(lon[i] - lon[j]);
                    double q2 = cos(lat[i] - lat[j]);
                    double q3 = cos(lat[i] + lat[j]);
                    fEdgeDis[i][j] =
                        (int)(RRR * acos(0.5 * ((1.0 + q1) * q2 - (1.0 - q1) * q3)) + 1.0);
                }
            }
        }
        else {
            printf("Unsupported EDGE_WEIGHT_TYPE: %s\n", type);
            exit(1);
        }
    }

    fclose(fp);

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

    Cost walked = 0;
    Cost cost = 0;

    for (int i = 0; i < sol.fN - 1; ++i) {
        int u = sol.fTour[i];
        int v = sol.fTour[i + 1];

        walked += fEdgeDis[u][v];
        cost += walked;
    }

    if (closed_tour())
        cost += walked + fEdgeDis[sol.fTour[sol.fN - 1]][sol.fTour[0]];

    sol.fEvaluationValue = cost;
}