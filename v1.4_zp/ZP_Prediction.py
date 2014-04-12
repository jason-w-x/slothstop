from datafetch import rapid_refresh
import math

TIMESTEP    = 1.0      # s 
GRAVITY     = 9.80655 
B_DRAG      = 0.5      # balloon drag coeff
P_DRAG      = 2.5      # parachute drag coeff
EARTH_RAD   = 6356.766 # Earth radius (m)
GAS_CONST_U = 8314.32  # universal gas const J/mol/K
GAS_CONST_A = 286.9    # air gas const
GAS_CONST_H = 2077     # helium gas const
M_PER_DEG   = 111120.0

dset = 0

class ZP_Prediction(object):
    def __init__(self, lat, lon, alt, timeout):
        self.time = 0.0
        self.lat = float(lat)
        self.lon = lon
        self.alt = alt
        self.is_timeup = False
        self.timeout = timeout
        self.ascent_pts  = []
        self.descent_pts = []
        self.rap = rapid_refresh()

    def set_params(self, tanks, payload, parachute, maxvol, ballmass):
        self.mass = payload*0.45359237 + ballmass/1000.0 #kg
        self.parachute = parachute*0.3048 #m
        
        tankvol = 43.8*0.001
        tanktemp = (70-32)*5.0/9.0 + 273.15
        tankpress = 14500*1000.0

        self.mol_hel = tanks*tankpress*tankvol/(GAS_CONST_U/1000)/tanktemp
        self.max_vol = maxvol

    def lin_interp(self, x0, x1, y0, y1, x):
        return (float((y1-y0)/(x1-x0)))*(x-x0) + y0

    def calc_vol(self, t, p):
        return self.mol_hel*(GAS_CONST_U/1000.0)*t/p

    def calc_mols(self, t, p, v):
        return v/((GAS_CONST_U/1000.0)*t/p)

    def calc_temp(self):
        if self.alt > self.rap.hght[dset][-1]:
            return self.rap.temp[dset][-1]
        if self.alt < self.rap.hght[dset][0]:
            return self.rap.temp[dset][0]
        
        for i in range(1, len(self.rap.hght[dset])):
            if self.alt <= self.rap.hght[dset][i] and \
                    self.alt > self.rap.hght[dset][i-1]:
                return self.lin_interp(self.rap.hght[dset][i-1], self.rap.hght[dset][i],
                                       self.rap.temp[dset][i-1], self.rap.temp[dset][i],
                                       self.alt)

    def calc_grav(self):
        return GRAVITY*((EARTH_RAD*1000)/(EARTH_RAD*1000+self.alt))**2

    def calc_density(self, t, p, gconst):
        return p/gconst/t

    def calc_press(self, temp):
        boltzmann = 1.38*(10**-23)
        mol_mass_a = 28.9645
        one_amu = 1.66*(10**-27)

        if self.alt > self.rap.hght[dset][-1]:
            g = self.calc_grav()
            p0 = self.rap.pres[dset][-1]
            h0 = self.rap.hght[dset][-1]

            return p0*math.exp(-(self.alt-h0)/(boltzmann*temp/(mol_mass_a*one_amu)/g))
        if self.alt < self.rap.hght[dset][0]:
            return self.rap.hght[dset][0]
        
        for i in range(1, len(self.rap.hght[dset])):
            if self.alt <= self.rap.hght[dset][i] and \
                    self.alt > self.rap.hght[dset][i-1]:
                return self.lin_interp(self.rap.hght[dset][i-1], self.rap.hght[dset][i],
                                       self.rap.pres[dset][i-1], self.rap.pres[dset][i],
                                       self.alt)

    def calc_asc_rate(self, lift, t, p, m):
        return (2*lift/(B_DRAG*math.pi*((3.0/(4.0*math.pi))**(2.0/3.0))*(GAS_CONST_H**(2.0/3.0))/GAS_CONST_A*(m**(2.0/3.0))*((p/t)**(1.0/3.0))))**0.5

    def calc_desc_rate(self, d, g):
        return (2*self.mass*g/(d*P_DRAG*math.pi*((self.parachute*(2.0/3.0)/2.0)**2)))**0.5
    

    def interpolateVEast(self):
        if self.alt > self.rap.hght[dset][-1]:
            return self.rap.veas[dset][-1]
        if self.alt < self.rap.hght[dset][0]:
            return self.rap.veas[dset][0]
        for i in range(1, len(self.rap.hght[dset])):
            if self.alt <= self.rap.hght[dset][i] and \
                    self.alt > self.rap.hght[dset][i-1]:
                return self.lin_interp(self.rap.hght[dset][i-1], self.rap.hght[dset][i],
                                       self.rap.veas[dset][i-1], self.rap.veas[dset][i],
                                       self.alt)

    def interpolateVNorth(self):
        if self.alt > self.rap.hght[dset][-1]:
            return self.rap.vnor[dset][-1]
        if self.alt < self.rap.hght[dset][0]:
            return self.rap.vnor[dset][0]
        for i in range(1, len(self.rap.hght[dset])):
            if self.alt <= self.rap.hght[dset][i] and \
                    self.alt > self.rap.hght[dset][i-1]:
                return self.lin_interp(self.rap.hght[dset][i-1], self.rap.hght[dset][i],
                                       self.rap.vnor[dset][i-1], self.rap.vnor[dset][i],
                                       self.alt)

    def ascent(self):
        t = self.calc_temp()

        p = self.calc_press(t)

        g = self.calc_grav()

        v = self.calc_vol(t,p)

        if v > self.max_vol:
            # calc new hel_mols
            v = self.max_vol
            self.mol_hel = self.calc_mols(t,p,v)

        atm_dens = self.calc_density(t, p, GAS_CONST_A)
        hel_dens = self.calc_density(t, p, GAS_CONST_H)

        hel_mass = hel_dens*v
        netlift = atm_dens*g*v - self.mass*g

        netlift = 0.0 if netlift < 0 else netlift
        asc_rate = self.calc_asc_rate(netlift, t, p, hel_mass)

        vnorth = self.interpolateVNorth()
        veast  = self.interpolateVEast()

        self.alt = self.alt + TIMESTEP*asc_rate
        self.lat = self.lat + vnorth*TIMESTEP
        self.lon = self.lon + veast*TIMESTEP

        self.ascent_pts.append((self.lat,self.lon))

    def descent(self):
        t = self.calc_temp()
        p = self.calc_press(t)

        g = self.calc_grav()

        atm_dens = self.calc_density(t, p, GAS_CONST_A)

        dsc_rate = self.calc_desc_rate(atm_dens, g)
        vnorth = self.interpolateVNorth()
        veast  = self.interpolateVEast()

        self.alt = self.alt - TIMESTEP*dsc_rate
        print('{0}\n'.format(vnorth))
        self.lat = self.lat + vnorth*TIMESTEP
        self.lon = self.lon + veast*TIMESTEP

        self.descent_pts.append((self.lat,self.lon))

    def mainloop(self):
        self.rap.read_station_list()

        self.ascent_pts.append((self.lat,self.lon))
        while self.alt > 200.0 or not self.is_timeup:
            dset = int(math.floor(self.time / 3600))
            if self.time % 300 == 0:
                self.rap.connect_and_fetch(self.lat, self.lon)

            if self.is_timeup:
                print('descent\n')
                self.descent()
            else: 
                print('ascent\n')
                self.ascent()
            
            self.time = self.time + TIMESTEP

            if self.time == self.timeout:
                self.is_timeup = True

            print('alt {0} timestep {1} of {2}\n'.format(self.alt, self.time, self.timeout))

        center_lat = (self.ascent_pts[0][0]+self.descent_pts[-1][0])/2
        center_lon = (self.ascent_pts[0][1]+self.descent_pts[-1][1])/2

        file = open('index.html', 'w')

        file.write('<!DOCTYPE html>\n')
        file.write('<html>\n')
        file.write('  <head>\n')
        file.write('    <meta name=\"viewport\" content =\"initial-scale=1.0, user-scalable=yes\" />\n')
        file.write('    <style type=\"text/css\">\n')
        file.write('      html { height: 100% } \n')
        file.write('      body { height: 75%; margin: 20; padding: 20 }\n')
        file.write('    </style>\n')
        file.write('    <script type=\"text/javascript\"\n')
        file.write('      src=\"http://maps.googleapis.com/maps/api/js?key=AIzaSyD60d34mCUoQ63hWqsCdZwwa1_Ywhm_4wE&sensor=true\">\n')
        file.write('    </script>\n')
        file.write('    <script type=\"text/javascript\">\n')
        file.write('      function initialize() {\n')
        file.write('        var mapOptions = {\n')
        file.write('           center: new google.maps.LatLng({0}, {1}),\n'.format(center_lat, center_lon))
        file.write('           zoom: 10,\n')
        file.write('           mapTypeId: google.maps.MapTypeId.ROADMAP\n')
        file.write('        };\n')
        file.write('\n')
        file.write('        var map = new google.maps.Map(document.getElementById(\"map_canvas\"),mapOptions);\n')

        file.write('        var pinColorR = \"FF6666\";\n')
        file.write('        var pinImageR = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|\" + pinColorR,\n')
        file.write('           new google.maps.Size(21, 34),\n')
        file.write('           new google.maps.Point(0,0),\n')
        file.write('           new google.maps.Point(10, 34));\n')
        file.write(' \n')
        file.write('        var pinColorG = \"66FF66\";\n')
        file.write('        var pinImageG = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|\" + pinColorG,\n')
        file.write('           new google.maps.Size(21, 34),\n')
        file.write('           new google.maps.Point(0,0),\n')
        file.write('           new google.maps.Point(10, 34));\n')
        file.write(' \n')
        file.write('        var pinColorB = \"6666FF\";\n')
        file.write('        var pinImageB = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|\" + pinColorB,\n')
        file.write('           new google.maps.Size(21, 34),\n')
        file.write('           new google.maps.Point(0,0),\n')
        file.write('           new google.maps.Point(10, 34));\n')
        file.write(' \n')
        file.write('        var pinColorY = \"FFFF66\";\n')
        file.write('        var pinImageY = new google.maps.MarkerImage(\"http://chart.apis.google.com/chart?chst=d_map_pin_letter&chld=%E2%80%A2|\" + pinColorY,\n')
        file.write('           new google.maps.Size(21, 34),\n')
        file.write('           new google.maps.Point(0,0),\n')
        file.write('           new google.maps.Point(10, 34));\n')
        file.write(' \n')

        file.write('        var marker = new google.maps.Marker({\n')
        file.write('           position: new google.maps.LatLng({0},{1}),\n'.format(self.ascent_pts[0][0],self.ascent_pts[0][1]))
        file.write('           icon: pinImageG,\n')
        file.write('           map: map\n')
        file.write('        });\n')
        file.write(' \n')

        file.write('        var marker = new google.maps.Marker({\n')
        file.write('           position: new google.maps.LatLng({0},{1}),\n'.format(self.descent_pts[-1][0],self.descent_pts[-1][1]))
        file.write('           icon: pinImageY,\n')
        file.write('           map: map\n')
        file.write('        });\n')
        file.write(' \n')

        file.write('        var marker = new google.maps.Marker({\n')
        file.write('           position: new google.maps.LatLng({0},{1}),\n'.format(self.descent_pts[0][0],self.descent_pts[0][1]))
        file.write('           icon: pinImageB,\n')
        file.write('           map: map\n')
        file.write('        });\n')
        file.write(' \n')

        file.write('var flightPlanCoordinates = [\n')

        for (lat,lon) in self.ascent_pts:
            file.write('  new google.maps.LatLng({0},{1}),\n'.format(lat,lon))

        for (lat,lon) in self.descent_pts:
            file.write('  new google.maps.LatLng({0},{1}),\n'.format(lat,lon))
            
        file.write('      ];\n')
        file.write('\n')
        file.write('      var flightPath = new google.maps.Polyline({\n')
        file.write('        path: flightPlanCoordinates,\n')
        file.write('        strokeColor: \"#FF0000\",\n')
        file.write('        strokeOpacity: 1.0,\n')
        file.write('        strokeWeight: 3\n')
        file.write('      });\n')
        file.write('\n')
        file.write('      flightPath.setMap(map);\n')
      
        # APRS here

        file.write('      }\n')
        file.write('    </script>\n')
        file.write('  </head>\n')
        file.write('  <body onload=\"initialize()\">\n')
        file.write('    <div id=\"map_canvas\" style=\"width:100%; height:100%\"></div>\n')
        file.write('    This is a Test\n')
        file.write('  </body>\n')
        file.write('</html>\n')

        file.close()

if __name__ == "__main__":
    zp = ZP_Prediction(41.9439, -85.6325, 301, 10800)
    zp.set_params(2, 10.59, 6.0, 113.267, 2830.42)

    zp.mainloop()
