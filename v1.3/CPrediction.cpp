#include "CPrediction.h"
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iostream>

#define TIMESTEP    1.0        // model time increment (s) 
#define GRAVITY     9.80665    
#define B_DRAG      0.5        // balloon drag coefficient
#define P_DRAG      1.5        // parachute drag coefficient
#define EARTH_RAD   6356.766
#define GAS_CONST_U 8314.32    // universal gas const J/mol/K
#define GAS_CONST_A 286.9      // air gas const J/mol/K
#define GAS_CONST_H 2077       // helium gas const J/mol/K
#define M_PER_DEG   111120     // meters/deg

using namespace std;

CPrediction::CPrediction()
{
  nData     = 0;
  burstCond = 0;
  burstDiam = 0;
  modelTime = 0;
  isBurst   = false;
  pData     = NULL;
  pAPRS     = NULL;
}

void CPrediction::getParams()
{
  cout << "Weight of Payload (pounds): ";
  cin >> massPayload;

  cout << "Weight of Balloon (grams): ";
  cin >> massBalloon;

  cout << "Number of Helium Tanks: ";
  cin >> helTanks;

  float diam;

  cout << "Measured Parachute Diameter (feet): ";
  cin >> diam;

  //convert to metric units
  massPayload  *= 0.45359237;
  diam         *= 0.3048;
  parachuteArea = M_PI * pow((diam * 2.0/3.0 / 2.0), 2);
}

void CPrediction::ARLreader(char* filename)
{
  ifstream file(filename);

  if(!file.is_open())
  {
    cerr << "Error: Unable to find input ARL file\n";
    exit(0);
  }

  file >> launchLoc.coords.lat >> launchLoc.coords.lon >> launchLoc.elev;
  file >> nData;

  nData++;

  pData = new data[nData];

  float garbage;

  for(int i = 1; i < nData; i++)
  {
    file >> pData[i].press >> pData[i].height >> pData[i].temp >> garbage >> pData[i].VEast >> pData[i].VNorth;

    pData[i].VEast  = pData[i].VEast / (M_PER_DEG * cos(launchLoc.coords.lat * M_PI / 180.0));
    pData[i].VNorth = pData[i].VNorth / M_PER_DEG;

  }

  file >> currentLoc.coords.lat >> currentLoc.coords.lon >> currentLoc.elev;
  file >> isBurst;
  file >> burstCond;

  file >> nAPRS;

  pAPRS = new coord[nAPRS];

  for(int i = 0; i < nAPRS; i++)
  {
    file >> pAPRS[i].lat >> pAPRS[i].lon;
    pAPRS[i].lon -= (pAPRS[i].lon > 0.0) ? 360.0 : 0.0;
  }

  // set default data vals for first data point

  pData[0].press  = pData[1].press;
  pData[0].height = 0.0;
  pData[0].temp   = pData[1].temp;
  pData[0].VEast  = pData[1].VEast;
  pData[0].VNorth = pData[1].VNorth;

  // convert pressure from hPa to Pa
  // convert temp from C to K

  for(int i = 0; i < nData; i++)
  {
    pData[i].temp  += 273.15;
    pData[i].press *= 100.0;
  }
}

void CPrediction::findKaymontBurst()
{
   float weights[13] = {200, 300, 350, 450, 500, 600, 700, 800, 1000, 1200, 1500, 2000, 3000};	/* balloon weights (grams) */
   float burstDiameter[13] = {300, 378, 412, 472, 499, 602, 653, 700, 786, 863, 944, 1054, 1300};	/* burst diameters from manufacturer specs (cm) */

   for(int i = 0; i < 13; i++)
   {
     if(weights[i] == massBalloon)
     {
       burstDiam = burstDiameter[i] / 100.0;
       return;
     }
   }
   cerr << "Error: Unable to determine burst diameter for specified balloon size.\n";
   exit(0);
}

void CPrediction::runPrediction()
{
  findKaymontBurst();

  calcForces();

  if(isBurst)
  {
    cout << "BURST!!!\n";
    burstLoc = currentLoc;
  }
  else
  {
    cout << "ASCENT!!!\n";
    ascentPrediction();
    cout << "Balloon predicted to burst at " << burstLoc.elev << "m\n";
  }
  cout << "DESCENT\n";
  descentPrediction();

  predictedToFile();
}

void CPrediction::ascentPrediction()
{
  float vr;
  geo tempGeo;
  float press, temp, gravity, atmDensity, helDensity, netLiftF, ascRate, vol, diam, vNorth, vEast;

  tempGeo = currentLoc;

  predicted.push_back(tempGeo);

  temp  = calcTemp(tempGeo.elev);
  press = calcPress(tempGeo.elev, temp);
	
  gravity = calcGravity(tempGeo.elev);
  atmDensity = calcDensity(temp, press, GAS_CONST_A);
  helDensity = calcDensity(temp, press, GAS_CONST_H);

  netLiftF = calcNetLiftForce(gravity);
  ascRate  = calcAscentRate(netLiftF, temp, press);

  vol  = calcVol(temp, press);
  diam = calcDiam(vol);

  while((diam <= burstDiam)) 
  { 
    //diameter check performed here so burst point writes to file successfully
    //if (predictedCounter > 0) diameter = newDiameter;
		
    tempGeo.elev += TIMESTEP * ascRate;

    modelTime += TIMESTEP;

    temp  = calcTemp(tempGeo.elev) * GetRandom();
    press = calcPress(tempGeo.elev, temp) * GetRandom();

    gravity = calcGravity( tempGeo.elev );

    atmDensity = calcDensity(temp, press, GAS_CONST_A);
    helDensity = calcDensity(temp, press, GAS_CONST_H);

    netLiftF = calcNetLiftForce(gravity);

    ascRate  = calcAscentRate(netLiftF, temp, press) * GetRandom();

    //calculate Velocity North and East
    vNorth = interpolateVNorth(tempGeo.elev);
    vr = 0.0001 * GetRandom() - 0.0001;
    vNorth = vNorth*GetRandom() + vr;

    vEast = interpolateVEast(tempGeo.elev);
    vr = 0.00015 * GetRandom() - 0.00015;
    vEast = vEast*GetRandom() + vr;

    tempGeo.coords.lat = calcLat(tempGeo.coords.lat, vNorth);
    tempGeo.coords.lon = calcLon(tempGeo.coords.lon, vEast);

    vol  = calcVol(temp, press);
    diam = calcDiam(vol);

    if(burstCond < 0.0) 
    {
      //  This is an altitude condition
      if(tempGeo.elev >= -burstCond) 
      {
	diam = burstDiam + 1.0;
      }
    }
    else if(burstCond > 0.0) 
    {
      //  This is a time condition
      if(modelTime >= burstCond) 
      {
	diam = burstDiam + 1.0;
      }
    }
    predicted.push_back(tempGeo);
  }
  burstLoc = tempGeo;
}


/*--------------------------------------------------------------------------------------*/
void CPrediction::descentPrediction()
{
  float vr;
  float press, temp, gravity, atmDensity, helDensity, netLiftF, descRate, vol, diam, vNorth, vEast;

  //to ensure first point is at correct time...
  modelTime -= TIMESTEP;
	
  geo tempGeo = burstLoc;
	
  if(isBurst) 
  {
    predicted.push_back(tempGeo);
  }

  while(tempGeo.elev >= launchLoc.elev) 
  {
    predicted.push_back(tempGeo);
	
    //increment time step
    modelTime += TIMESTEP;

    temp  = calcTemp(tempGeo.elev) * GetRandom();
    press = calcPress(tempGeo.elev, temp) * GetRandom();

    atmDensity = calcDensity(temp, press, GAS_CONST_A);
    gravity    = calcGravity(tempGeo.elev);

    descRate = calcDescentRate(atmDensity, gravity) * GetRandom();
    tempGeo.elev -= TIMESTEP * descRate;

    vNorth = interpolateVNorth(tempGeo.elev);
    vEast  = interpolateVEast(tempGeo.elev);

    //calculate balloon velocity and new position in north/south direction
    // Add a little bit of error just to give some randomness.
    vr = 0.0001 * GetRandom() - 0.0001;
    vNorth = vNorth * GetRandom() + vr;
    tempGeo.coords.lat = calcLat(tempGeo.coords.lat, vNorth);

    vr = 0.00015 * GetRandom() - 0.00015;
    vEast = vEast * GetRandom() + vr;
    tempGeo.coords.lon = calcLon(tempGeo.coords.lon, vEast);
  }
}

float CPrediction::GetRandom() 
{
  float RandomPercent = 0; // just for now
  return 1.0 + (rand() / RAND_MAX - 0.5) * 2.0 * RandomPercent;
}

void CPrediction::calcHelAmt() /*determine amount of helium in balloon */
{
  float tankVolume;	//cubic meters
  float tankTemperature;	//Kelvin
  float tankPressure;	//Pascals

  /* Based on measurements of tanks at AOSS loading dock.
     Assumes we're using K-size gas cylinders
     
     Wikipedia says interior tank volume is 43.8 liters
     Yes, I know, Wikipedia...I'm ashamed too. */
  tankVolume = 43.8 * 0.001; //cubic meters

  //assumes tank temperature of 70 degrees Fahrenheit
  tankTemperature = (70 - 32) * 5.0 / 9.0 + 273.15;

  //based on measurements taken with tanks at loading dock
  tankPressure = 14500 * 1000.0;

  //calculate number of moles of gas in tank based on ideal gas law
  numMol = helTanks * tankPressure * tankVolume / (GAS_CONST_U / 1000.0) / tankTemperature;
}

void CPrediction::calcForces()
{
  calcHelAmt();

  //determine total upward lift force by using ground values
  //this value is assumed to be constant throughout entire flight (assumed no helium lost)
  float height = pData[1].height;
  float temp   = pData[1].temp;
  float press  = pData[1].press;
  float volume = calcVol( temp,press );
  float diam   = calcDiam( volume );

  float helDensity = calcDensity(temp,press, GAS_CONST_H);
  massHel    = helDensity * volume;
  totalLiftF = (1.0 / GAS_CONST_A - 1.0 / GAS_CONST_H) * (massHel * GAS_CONST_H);
}

float CPrediction::calcTemp(float height)  
{
  if(height > pData[nData-1].height)
  {
    return pData[nData-1].temp;
  }
  else if(height <= pData[0].height)
  {
    return pData[0].temp;
  }
  else 
  {
    for(int i = 1; i < nData; i++) 
    {
      if((height <= pData[i].height) && (height > pData[i-1].height))
      {
	return linearInterp(pData[i-1].height, pData[i].height, pData[i-1].temp, pData[i].temp, height);
      }
    }
  }
}

float CPrediction::calcPress(float height, float temp)
{
  float pressure0 = pData[nData-1].press;	//"initial pressure" at end of ARL data (Pa)
  float height0   = pData[nData-1].height;	//"initial height" at end of ARL data (m)
  float gravity;	                        //gravity at input height

  float boltzmann = 1.38 * pow(10, -23);	//Boltzmann constant; J/K
  float molarMassAir = 28.9645;	//g/mol
  float oneAMU = 1.66 * pow(10, -27);	//kg

  if(height > pData[nData-1].height) 
  {
    gravity = calcGravity(height);
    return pressure0 * exp(-(height - height0) / (boltzmann * temp / (molarMassAir * oneAMU) / gravity));
  } 
  else if(height <= pData[0].height) 
  {
    gravity = calcGravity(height);
    return pData[0].press;
  } 
  else 
  {
    for(int i = 1; i < nData; i++) 
    {
      if((height <= pData[i].height) && (height > pData[i-1].height)) 
      {
	return linearInterp(pData[i-1].height, pData[i].height, pData[i-1].press, pData[i].press, height);
      }
    }
  }
}

float CPrediction::calcGravity(float height)
{
   return GRAVITY * pow(((EARTH_RAD * 1000) / (EARTH_RAD * 1000 + height)), 2);
}

float CPrediction::calcDensity(float temp, float press, float gasConst)
{
  return press / gasConst / temp;
}

float CPrediction::calcNetLiftForce(float gravity)
{
  return (totalLiftF - massPayload - massBalloon / 1000) * gravity;
}

float CPrediction::calcAscentRate(float liftF, float temp, float press)
{
  return sqrt(2 * liftF / (B_DRAG * M_PI * pow((3.0 / (4.0 * M_PI)), (2.0 / 3.0)) * 
               pow(GAS_CONST_H, (2.0 / 3.0)) / GAS_CONST_A * 
	       pow(massHel, (2.0 / 3.0)) * pow((press / temp), (1.0 / 3.0))));
}

float CPrediction::calcDescentRate(float density, float gravity)
{
  return sqrt(2 * massPayload * gravity / (density * P_DRAG * parachuteArea));
}

float CPrediction::calcVol(float temp, float press)
{
  return numMol * (GAS_CONST_U / 1000.0) * temp / press;
}

float CPrediction::calcDiam(float volume)
{
  return 2.0 * pow((3.0 * volume / (4.0 * M_PI)), (1.0 / 3.0));
}

float CPrediction::interpolateVEast(float height) 
{
  if(height > pData[nData-1].height)
  {
    return pData[nData-1].VEast;
  }
  else
  {
    for(int i = 1; i < nData; i++)
    {
      if((height <= pData[i].height) && (height > pData[i-1].height))
      {
	return linearInterp(pData[i-1].height, pData[i].height, pData[i-1].VEast, pData[i].VEast, height);
      }
    }
  }
}

float CPrediction::interpolateVNorth(float height) 
{
  if(height > pData[nData-1].height)
  {
    return pData[nData-1].VNorth;
  }
  else
  {
    for(int i = 1; i < nData; i++)
    {
      if((height <= pData[i].height) && (height > pData[i-1].height))
      {
	return linearInterp(pData[i-1].height, pData[i].height, pData[i-1].VNorth, pData[i].VNorth, height);
      }
    }
  }
}

float CPrediction::calcLat(float lat, float VNorth)
{
  return lat + VNorth * TIMESTEP;
}

float CPrediction::calcLon(float lon, float VEast)
{
  return lon + VEast * TIMESTEP;
}

float CPrediction::linearInterp(float x0, float x1, float y0, float y1, float x)
{
  return (y1 - y0) / (x1 - x0) * (x - x0) + y0;
}

void CPrediction::predictedToFile()
{
  int q;
  float IncludeAlt = 0.01;
  float CenterLat, CenterLon, OtherLat, OtherLon;
  float MinLatLat, MinLatLon, MaxLatLat, MaxLatLon;
  float MinLonLat, MinLonLon, MaxLonLat, MaxLonLon;
  float dLat, dLon, Zoom, ZoomTest;
  int iZoom;
  FILE *html;
  int iTime;

  MinLatLat = 90.0;
  MaxLatLat = -90.0;
  MinLonLon = 360.0;
  MaxLonLon = -360.0;

  dLon = (MaxLonLon - MinLonLon) * cos(predicted.back().coords.lat * M_PI / 180.0);

  Zoom = dLat;
  if (dLon > Zoom) Zoom = dLon;
  Zoom = Zoom * 111000.0;
  iZoom = 21;
  ZoomTest = 20.0;
  while (ZoomTest < Zoom) {
    ZoomTest = ZoomTest*2.0;
    iZoom--;
  }

  //  printf("dLat, dLon, Zoom, ZoomTest, iZoom : %f %f %f %f %d\n",dLat, dLon, Zoom, ZoomTest, iZoom);

  CenterLat = (predicted.front().coords.lat + predicted.back().coords.lat)/2.0;
  CenterLon = (predicted.front().coords.lon + predicted.back().coords.lon)/2.0;

  dLon = fabs(predicted.back().coords.lon - predicted.front().coords.lon);
  dLat = fabs(predicted.back().coords.lat - predicted.front().coords.lat);

  Zoom = dLat;
  if (dLon > Zoom) Zoom = dLon;

  Zoom = dLat;
  if (dLon > Zoom) Zoom = dLon;
  Zoom = Zoom * 111000.0;
  iZoom = 22;
  ZoomTest = 20.0;
  while (ZoomTest < Zoom) {
    ZoomTest = ZoomTest*2.0;
    iZoom--;
  }

  
  html = fopen("index.html","w");


  fprintf(html,"<!DOCTYPE html>\n");
  fprintf(html,"<html>\n");
  fprintf(html,"  <head>\n");
  fprintf(html,"    <meta name=\"viewport\" content=\"initial-scale=1.0, user-scalable=yes\" />\n");
  fprintf(html,"    <style type=\"text/css\">\n");
  fprintf(html,"      html { height: 100%% } \n");
  fprintf(html,"      body { height: 75%%; margin: 20; padding: 20 }\n");
  fprintf(html,"    </style>\n");
  fprintf(html,"    <script type=\"text/javascript\"\n");
  fprintf(html,"      src=\"http://maps.googleapis.com/maps/api/js?key=AIzaSyD60d34mCUoQ63hWqsCdZwwa1_Ywhm_4wE&sensor=true\">\n");
  fprintf(html,"    </script>\n");
  fprintf(html,"    <script type=\"text/javascript\">\n");
  fprintf(html,"      function initialize() {\n");
  fprintf(html,"        var mapOptions = {\n");
  fprintf(html,"           center: new google.maps.LatLng(%f, %f),\n",CenterLat,CenterLon);
  fprintf(html,"           zoom: %d,\n",iZoom);
  fprintf(html,"           mapTypeId: google.maps.MapTypeId.ROADMAP\n");
  fprintf(html,"        };\n");
  fprintf(html,"\n");
  fprintf(html,"        var map = new google.maps.Map(document.getElementById(\"map_canvas\"),mapOptions);\n");

  fprintf(html,"        var pinColorR = \"FF6666\";\n");
  fprintf(html,"        var pinImageR = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%%E2%%80%%A2|\" + pinColorR,\n");
  fprintf(html,"           new google.maps.Size(21, 34),\n");
  fprintf(html,"           new google.maps.Point(0,0),\n");
  fprintf(html,"           new google.maps.Point(10, 34));\n");
  fprintf(html," \n");
  fprintf(html,"        var pinColorG = \"66FF66\";\n");
  fprintf(html,"        var pinImageG = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%%E2%%80%%A2|\" + pinColorG,\n");
  fprintf(html,"           new google.maps.Size(21, 34),\n");
  fprintf(html,"           new google.maps.Point(0,0),\n");
  fprintf(html,"           new google.maps.Point(10, 34));\n");
  fprintf(html," \n");
  fprintf(html,"        var pinColorB = \"6666FF\";\n");
  fprintf(html,"        var pinImageB = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%%E2%%80%%A2|\" + pinColorB,\n");
  fprintf(html,"           new google.maps.Size(21, 34),\n");
  fprintf(html,"           new google.maps.Point(0,0),\n");
  fprintf(html,"           new google.maps.Point(10, 34));\n");
  fprintf(html," \n");
  fprintf(html,"        var pinColorY = \"FFFF66\";\n");
  fprintf(html,"        var pinImageY = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%%E2%%80%%A2|\" + pinColorY,\n");
  fprintf(html,"           new google.maps.Size(21, 34),\n");
  fprintf(html,"           new google.maps.Point(0,0),\n");
  fprintf(html,"           new google.maps.Point(10, 34));\n");
  fprintf(html," \n");

  fprintf(html,"        var marker = new google.maps.Marker({\n");
  fprintf(html,"           position: new google.maps.LatLng(%f,%f),\n", predicted.front().coords.lat,predicted.front().coords.lon);
  fprintf(html,"           icon: pinImageG,\n");
  fprintf(html,"           map: map\n");
  fprintf(html,"        });\n");
  fprintf(html," \n");

  fprintf(html,"        var marker = new google.maps.Marker({\n");
  fprintf(html,"           position: new google.maps.LatLng(%f,%f),\n", predicted.back().coords.lat,predicted.back().coords.lon);
  fprintf(html,"           icon: pinImageY,\n");
  fprintf(html,"           map: map\n");
  fprintf(html,"        });\n");
  fprintf(html," \n");

  fprintf(html,"        var marker = new google.maps.Marker({\n");
  fprintf(html,"           position: new google.maps.LatLng(%f,%f),\n", burstLoc.coords.lat, burstLoc.coords.lon );
  fprintf(html,"           icon: pinImageB,\n");
  fprintf(html,"           map: map\n");
  fprintf(html,"        });\n");
  fprintf(html," \n");

  fprintf(html,"var flightPlanCoordinates = [\n");

  for ( q = 0; q < predicted.size(); q++ )
    fprintf(html,"  new google.maps.LatLng(%f,%f),\n",predicted[q].coords.lat, predicted[q].coords.lon );

  fprintf(html,"      ];\n");
  fprintf(html,"\n");
  fprintf(html,"      var flightPath = new google.maps.Polyline({\n");
  fprintf(html,"        path: flightPlanCoordinates,\n");
  fprintf(html,"        strokeColor: \"#FF0000\",\n");
  fprintf(html,"        strokeOpacity: 1.0,\n");
  fprintf(html,"        strokeWeight: 3\n");
  fprintf(html,"      });\n");
  fprintf(html,"\n");
  fprintf(html,"      flightPath.setMap(map);\n");

  if (nAPRS > 0) {

    fprintf(html,"        var marker = new google.maps.Marker({\n");
    fprintf(html,"           position: new google.maps.LatLng(%f,%f),\n",pAPRS[0].lat, pAPRS[0].lon );
    fprintf(html,"           icon: pinImageY,\n");
    fprintf(html,"           map: map\n");
    fprintf(html,"        });\n");
    fprintf(html," \n");

    fprintf(html,"var APRSFlightCoordinates = [\n");
    for (q = 0; q < nAPRS; q++)
      fprintf(html,"  new google.maps.LatLng(%f,%f),\n",pAPRS[q].lat, pAPRS[q].lon);

    fprintf(html,"      ];\n");
    fprintf(html,"\n");
    fprintf(html,"      var APRSflightPath = new google.maps.Polyline({\n");
    fprintf(html,"        path: APRSFlightCoordinates,\n");
    fprintf(html,"        strokeColor: \"#0000FF\",\n");
    fprintf(html,"        strokeOpacity: 1.0,\n");
    fprintf(html,"        strokeWeight: 3\n");
    fprintf(html,"      });\n");
    fprintf(html,"\n");
    fprintf(html,"      APRSflightPath.setMap(map);\n");
  }


  fprintf(html,"      }\n");
  fprintf(html,"    </script>\n");
  fprintf(html,"  </head>\n");
  fprintf(html,"  <body onload=\"initialize()\">\n");
  fprintf(html,"    <div id=\"map_canvas\" style=\"width:100%%; height:100%%\"></div>\n");
  fprintf(html,"    This is a Test\n");
  fprintf(html,"  </body>\n");
  fprintf(html,"</html>\n");

  fclose(html);
}

CPrediction::~CPrediction()
{
  delete[] pData;
  delete[] pAPRS;
}
