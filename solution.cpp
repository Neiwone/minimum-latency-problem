#ifndef __SOLUTION__
#include "solution.h"
#endif

Solution::Solution() {                
    fN = 0;
    fTour = NULL;
    fEvaluationValue = 0;
}
 

Solution::~Solution() {
    delete [] fTour;
}


void Solution::Define( int N ) {
    fN = N;
    
    fTour = new int [ fN ];
}

Solution::Solution(const Solution& src) {
    fN = src.fN;
    fEvaluationValue = src.fEvaluationValue;

    if (fN > 0) {
        fTour = new int[fN];
        for (int i = 0; i < fN; ++i)
            fTour[i] = src.fTour[i];
    } else {
        fTour = NULL;
    }
}



Solution& Solution::operator=(const Solution& src) {
    if (this == &src) return *this;

    if (fN != src.fN) {
        delete[] fTour;
        fN = src.fN;
        fTour = new int[fN];
    }

    for (int i = 0; i < fN; ++i)
        fTour[i] = src.fTour[i];

    fEvaluationValue = src.fEvaluationValue;

    return *this;
}


bool Solution::operator == ( const Solution& src ) {
    if ( fN != src.fN ) return false;

    for ( int i = 0; i < fN; ++i ) {
        if ( fTour[i] != src.fTour[i] ) return false;
    }

    return true;

}