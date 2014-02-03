#ifndef CPREDICTION_H
#define CPREDICTION_H

#include <vector>

typedef struct dataType
{
  float height;   // m
  float temp;     // K
  float press;    // Pa
  float VEast;    // m/s
  float VNorth;   // m/s
} data;

typedef struct coordType
{
  float lat;
  float lon;
} coord;

typedef struct geoType
{
  coord coords;
  float elev;
} geo;

class CPrediction
{
  int nData;
  int nAPRS;

  geo launchLoc; 
  geo currentLoc;
  geo burstLoc;

  float burstDiam;

  float massPayload;
  float massBalloon;
  float helTanks;
  float parachuteArea;

// values used in density/asc/desc rate calcs
  float numMol;
  float totalLiftF;
  float massHel;

  float burstCond;
  data* pData;
  coord* pAPRS;
  
  float modelTime; // used to simulate model

  std::vector<geo> predicted;

  bool isBurst;

// mathematical functions
  float GetRandom();

  void calcForces();

  void calcHelAmt();
  float calcTemp(float);
  float calcPress(float, float);
  float calcGravity(float);
  float calcDensity(float, float, float);
  float calcNetLiftForce(float);
  float calcAscentRate(float, float, float);
  float calcDescentRate(float, float);
  float calcVol(float, float);
  float calcDiam(float);
  float interpolateVNorth(float);
  float interpolateVEast(float);
  float calcLat(float, float);
  float calcLon(float, float);
  float linearInterp(float, float, float, float, float);

// wrapper functions
  void findKaymontBurst();
  void ascentPrediction();
  void descentPrediction();
  void predictedToFile();

 public:
  CPrediction();
  void getParams();
  void ARLreader(char*);
  void runPrediction();
  ~CPrediction();
};

#endif
