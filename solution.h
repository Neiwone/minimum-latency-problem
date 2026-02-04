#ifndef __SOLUTION__
#define __SOLUTION__


#include <bits/stdc++.h>
using namespace std;

class Solution {
public:
    Solution();
    ~Solution();
    void Define( int N );
    Solution(const Solution& src);                  /* Copy constructor */
    Solution& operator = ( const Solution& src );   /* Copy */
    bool operator == (  const Solution& other );    /* Return true if two tours are the same, false otherwise */

    int fN;                     /* Number of cities */
    int* fTour;                 /* Route permutation */
    int fEvaluationValue;       /* Tour evaluation value */
    double* x;                  /* x[i] = x-coordinate of i */
    double* y;                  /* y[i] = y-coordinate of i */ 
    int** fDist;                /* fDist[i][j] = distance between i and j */
};

#endif