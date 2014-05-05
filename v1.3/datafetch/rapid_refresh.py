import re
import math
import time
from ftplib import FTP

RAP_LOCS = { (42.77, -84.60):'rap_klan',
             (42.27, -84.47):'rap_kjxn',
             (42.30, -85.25):'rap_kbtl',
             (42.88, -85.52):'rap_kgrr',
             (42.75, -86.10):'rap_biv',
             (42.41, -86.28):'rap_lwa',
             (42.23, -85.55):'rap_kazo',
             (43.17, -86.25):'rap_kmkg',
             (43.58, -86.24):'rap_kldm',
             (43.43, -85.30):'rap_krqb',
             (43.37, -84.44):'rap_kmop',
             (42.97, -83.75):'rap_kfnt'}

class rapid_refresh(object):    
    def __init__(self):
        self.elev = None
        self.lat  = None
        self.lon  = None
        self.time = None
        
        # list of list of tuples (hght pres temp windnorth windeast)
        #                          m    mPa   C      rad     rad
        self.data = []  
        self.hght = []  # height (m)
        self.pres = []  # pressure (mPa = hba)
        self.temp = []  # temp (C)
        self.vnor = []  # wind direction north (rad)
        self.veas = []  # wind direction east (rad)

    def nearest_station(self, lat_s, lon_s):
        min_dist = float('inf')
        closest_name = None
        for (lat, lon), name in RAP_LOCS.iteritems():
            dlat = lat_s-lat
            dlon = lon_s-lon
            dist = math.sqrt(dlat*dlat + dlon*dlon)
            if dist < min_dist:
                closest_name = name
                min_dist = dist            

        return closest_name

    def connect_and_fetch(self, lat, lon):
        filename = 'buf'
        file = open(filename,'w')
        print("Connecting to ftp server\n")
        ftp = FTP('ftp.meteo.psu.edu')
        print("Logging on to ftp server\n")
        ftp.login()       # login using user=anonymous pass=anonymous@
        
        ftp.cwd('pub/bufkit/RAP')        

        print("Retrieving data lines\n")
        station = self.nearest_station(lat, lon)
        ftp.retrlines('RETR {0}.buf'.format(station), lambda str, w=file.write: w(str+'\n'))
        
        print("Closing connection\n")
        file.close()
        ftp.quit()

        self.lat = lat
        self.lon = lon
        return filename

    def parse_file(self, filename):
        print("Parsing weather data\n")
        file = open(filename,'r')
        
        done = False
        
        # search for lat/lon/elev/initial time
        for line in file:
            r = re.findall(r'STID.*TIME = .*\/(.*)\n',line)
            if r:
                self.time = r[0]
                continue
        
            r = re.findall(r'SLAT = (.+) SLON = (.+) SELV = (.+)\n', line)
            if r:
                #self.lat  = float(r[0][0])
                #self.lon  = float(r[0][1])
                self.elev = float(r[0][2])
                break

        iter = file.__iter__()
        while not done:
            line1 = iter.next()
            r = re.findall(r'CFRL HGHT\n', line1)
            if not r:
                continue

            dat = []
            
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
                p = float(r[0][0])
                t = float(r[0][1])
                
                winddir = float(r[0][2])
                windspd = float(r[0][3]) * 0.514444  # knots to m/s

                n = windspd * math.sin(math.radians(270.0-winddir))
                e = windspd * math.cos(math.radians(270.0-winddir))
                
                r = re.findall(r'.+ (.+)\n', line2)
                h = float(r[0])

                dat.append((h, p, t, n, e))

            self.data.append(dat)
        file.close()
        
if __name__ == "__main__":
    # used for testing
    rap = rapid_refresh()
    filename = rap.connect_and_fetch(42, -85)
    rap.parse_file(filename)
    

    
