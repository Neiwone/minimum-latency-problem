#ifndef __EVALUATOR__
#define __EVALUATOR__

#ifndef __SOLUTION__
#include "solution.h"
#endif

#include <bits/stdc++.h>
using namespace std;

/* EUC_2D rounding: truncation (the project's default since the start) or
   TSPLIB's nint, needed to compare against costs published in the literature.
   Set before SetInstance. */
void set_euc_nint(bool on);
bool euc_nint();

class Evaluator {
public:
    Evaluator();
    ~Evaluator();
    void SetInstance(char filename[]);   /* Set the instance */
    void DoIt(Solution& sol);            /* Set the value of sol.fEvaluationValue */

    int fNearNumMax;    /* Maximum number of k (see below) */
    int **fNearCity;    /* NearCity[i][k]: k-th nearest city from i */
    int **fEdgeDis;     /* EdgeDis[i][j]: distance between i and j */
    int Ncity;          /* Number of cities */
    double *x;          /* x[i]: x-coordinate of i */
    double *y;          /* y[i]: y-coordinate of i */
};

#endif


