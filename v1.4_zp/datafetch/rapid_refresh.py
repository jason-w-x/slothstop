import re
import math
import sys
import time
from ftplib import FTP

M_PER_DEG = 111120

class rapid_refresh(object):
    
    def __init__(self):        
        self.elev = None
        self.lat  = None
        self.lon  = None
        self.time = None
        self.hght = []  # height (m)
        self.pres = []  # pressure (mPa = hba)
        self.temp = []  # temp (C)
        self.vnor = []  # wind direction north (rad)
        self.veas = []  # wind direction east (rad)
        self.stationlist = []

    def read_station_list(self):
        file = open('datafetch/StationList','r')

        for line in file:
            r = re.findall(r'(.+) SLAT = (.+) SLON = (.+) SELV = (.+)\r',line)
            if r:
                self.stationlist.append((r[0][0], float(r[0][1]), float(r[0][2]), r[0][3]))
    
    def calc_dist(self, x1, y1, x2, y2):
        return ((x2-x1)**2 + (y2-y1)**2)**0.5

    def find_nearest_station(self, lat, lon):
        min_dist = sys.float_info.max
        min_name = None
        for (sname, slat, slon, selv) in self.stationlist:
            dist = self.calc_dist(slat, slon, lat, lon)
            if dist < min_dist:
                min_dist = dist
                min_name = sname
        
        return min_name

    def connect_and_fetch(self, lat, lon):
        filename = 'buf'
        file = open(filename,'w')
        ftp = FTP('ftp.meteo.psu.edu')
        ftp.login()       # login using user=anonymous pass=anonymous@
        
        ftp.cwd('pub/bufkit/RAP')        

        station = self.find_nearest_station(lat, lon)
        print(station)
        ftp.retrlines('RETR rap_{0}.buf'.format(station), lambda str, w=file.write: w(str+'\n'))
        
        file.close()
        ftp.quit()
        
        self.parse_file(filename)

    def parse_file(self, filename):
        file = open(filename,'r')
        
        done = False
        
        print('clearing\n')
        self.hght = []  # height (m)
        self.pres = []  # pressure (mPa = hba)
        self.temp = []  # temp (C)
        self.vnor = []  # wind direction north (rad)
        self.veas = []  # wind direction east (rad)

        # search for lat/lon/elev/initial time
        for line in file:
            r = re.findall(r'STID.*TIME = .*\/(.*)\n',line)
            if r:
                self.time = r[0]
                continue
        
            r = re.findall(r'SLAT = (.+) SLON = (.+) SELV = (.+)\n', line)
            if r:
                self.lat  = r[0][0]
                self.lon  = r[0][1]
                self.elev = r[0][2]
                break

        iter = file.__iter__()
        while not done:
            line1 = iter.next()
            r = re.findall(r'CFRL HGHT\n', line1)
            if not r:
                continue

            h = []
            p = []
            t = []
            n = []
            e = []
            
            # search for weather data
            while True:
                line1 = iter.next()
                if line1 == '\n':
                    break
                if line1.startswith('STN'):
                    done = True
                    break
                line2 = iter.next()
                
                r = re.findall(r'(.+) (.+) .+ .+ .+ (.+) (.+) .+\n', line1)
                p.append(float(r[0][0])*100.0)
                t.append(float(r[0][1])+273.15)
                
                winddir = float(r[0][2])
                windspd = float(r[0][3]) * 0.514444  # knots to m/s

                n.append(windspd * math.sin(math.radians(270.0-winddir))/M_PER_DEG)
                e.append((windspd * math.cos(math.radians(270.0-winddir)))/M_PER_DEG)

                r = re.findall(r'.+ (.+)\n', line2)
                h.append(float(r[0]))

            self.hght.append(h)
            self.pres.append(p)
            self.temp.append(t)
            self.vnor.append(n)
            self.veas.append(e)
        file.close()

        

if __name__ == "__main__":
    # used for testing
    rap = rapid_refresh()
    rap.read_station_list()
    rap.connect_and_fetch(46.4, -86.4)
    #filename = rap.connect_and_fetch()
    #rap.parse_file(filename)
    

    
