#include <cstdlib>
#include <iostream>
#include "CPrediction.h"

using namespace std;

int main(int argc, char** argv)
{
    if(argc != 2)
    {
        cerr << "Error: Usage is \"run <ARL file name>\"\n";
        exit(0);
    }

    CPrediction prediction;

    prediction.getParams();
    prediction.ARLreader(argv[1]);

    prediction.runPrediction();

    cout << "Prediction end\n";

    return 0;
}
