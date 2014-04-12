from datafetch import rapid_refresh
import math

TIMESTEP    = 1.0      # s 
GRAVITY     = 9.80655 
B_DRAG      = 0.5      # balloon drag coeff
P_DRAG      = 1.5      # parachute drag coeff
EARTH_RAD   = 6356.766 # Earth radius (m)
GAS_CONST_U = 8314.32  # universal gas const J/mol/K
GAS_CONST_A = 286.9    # air gas const
GAS_CONST_H = 2077     # helium gas const

rap = rapid_refresh()
dset = 0

class ZP_Prediction(object):
    def __init__(self, lat, lon, alt):
        self.time = 0.0
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.is_timeup = False

    def set_params(self, tanks, payload, parachute, maxvol, ballmass):
        self.mass = payload + ballmass
        self.parachute = parachute
        
        tankvol = 43.8*0.001
        tanktemp = (70-32)*5.0/9.0 + 273.15
        tankpress = 14500*1000.0

        self.mol_hel = tanks*tankpress*tankvol/(GAS_CONST_U/1000)/tanktemp
        self.max_vol = maxvol

    def lin_interp(self, x0, x1, y0, y1, x):
        return (y1-y0)/(x1-x0)*(x-x0) + y0

    def calc_vol(self, t, p):
        return self.mol_hel*(GAS_CONST_U/1000.0)*t/p

    def calc_mols(self, t, p, v):
        return v/((GAS_CONST_U/1000.0)*t/p)

    def calc_temp(self):
        if self.alt > rap.hght[dset][-1]:
            return rap.temp[dset][-1]
        if self.alt < rap.hght[dset][0]:
            return rap.temp[dset][0]
        
        for i in range(1, rap.hght[dset].length):
            if self.alt <= rap.hght[dset][i] and \
               self.alt > rap.hght[dset][i-1]:
                return self.lin_interp(rap.hght[dset][i-1], rap.hght[dset][i],
                                       rap.temp[dset][i-1], rap.temp[dset][i],
                                       self.alt)

    def calc_grav(self):
        return GRAVITY*((EARTH_RAD*1000)/(EARTH_RAD*1000+self.alt))**2

    def calc_density(self, t, p, gconst):
        return p/gconst/t

    def calc_press(self, temp):
        boltzmann = 1.38*(10**-23)
        mol_mass_a = 28.9645
        one_amu = 1.66*(10**-27)

        if self.alt > rap.hght[dset][-1]:
            g = self.calc_grav()
            p0 = rap.press[dset][-1]
            h0 = rap.hght[dset][-1]

            return p0*math.exp(-(self.alt-h0)/(boltzmann*temp/(mol_mass_a*one_amu)/g))
        if self.alt < rap.hght[dset][0]:
            return rap.hght[dset][0]
        
        for i in range(1, rap.hght[dset].length):
            if self.alt <= rap.hght[dset][i] and \
               self.alt > rap.hght[dset][i-1]:
                return self.lin_interp(rap.hght[dset][i-1], rap.hght[dset][i],
                                       rap.press[dset][i-1], rap.press[dset][i],
                                       self.alt)

    def calc_net_lift(self, g):
        return 

    def ascent(self):
        t = self.calc_temp()
        p = self.calc_press(t)

        g = self.calc_grav()

        v = self.calc_vol(t,p)

        if v > self.max_vol:
            # calc new hel_mols
            v = self.max_vol
            self.mol_hel = self.calc_mols(t,p,v)

        #netlift = 
        atm_dens = self.calc_density(t, p, GAS_CONST_A)
        hel_dens = self.calc_density(t, p, GAS_CONST_H)
        pass

    def descent(self):
        pass

    def mainloop(self):
        rap.read_station_list()

        while self.alt > 200.0 and not self.is_timeup:
            file = rap.connect_and_fetch(self.lat, self.lon)
            rap.parse_file(file)
            dset = int(math.floor(self.time / 3600))

            if self.is_timeup: 
                self.descent() 
            else: 
                self.ascent()
            
            self.time = self.time + TIMESTEP

if __name__ == "__main__":
    zp = ZP_Prediction(41.75, -86.05, 201)
    zp.set_params(2, 10.59, 6.0, 113.267, 2830.42)

    zp.mainloop()
