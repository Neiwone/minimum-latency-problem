#ifndef __EVALUATOR__
#define __EVALUATOR__

#ifndef __SOLUTION__
#include "solution.h"
#endif

#include <bits/stdc++.h>
using namespace std;

/* EUC_2D rounding. Auto follows the literature of each MLP variant: the
   Hamiltonian path (Salehipour et al. 2011; Silva et al. 2012, Table 2)
   rounds down, the circuit (--closed: Abeledo et al. 2010; Bulhoes et al.
   2018; Santana et al. 2019, Table 1) uses TSPLIB's nint. Nint/Trunc force
   one. Set before SetInstance, after set_closed_tour; euc_nint() then says
   what the instance got. See docs/concepts/distance-types.md. */
enum class EucRound { Auto, Nint, Trunc };
void set_euc_round(EucRound mode);
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


