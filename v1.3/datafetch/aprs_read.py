import math
import re

class aprs_read(object):
    def __init__(self):
        self.has_burst = False
        self.time = []  # time (mystery units)
        self.hght = []  # height (m)
        self.lat  = []  # used only to print prev points
        self.lon  = []  # used only to print prev points
        self.vnor = []  # wind speed north (m/s)
        self.veas = []  # wind speed east (m/s)

    def read_xml(self, filename):
        try:
            file = open(filename, 'r')
        except IOError:
            print("No aprs\n")
            return None# file doesn't exist yet

        timeold = 0.0
        hghtold = None
        latold  = None
        lonold  = None

        burst1 = False
        burst2 = False
        burst3 = False
        print("Parsing APRS data\n")
        for line in file:
            r = re.findall('<time>(.+)</time><lat>(.+)</lat><lng>(.+)</lng><alt>(.+)</alt>', line)
            if r:
                time = float(r[0][0])
                lat  = float(r[0][1])
                lon  = 360.0 + float(r[0][2])
                alt  = float(r[0][3])

                dt = time-timeold
                if dt > 0:
                    if latold:
                        dr = math.radians(6372000.0+alt)
                        correction = math.cos(math.radians(lat))
                        vn = (lat-latold)/dt*dr
                        ve = (lon-lonold)/dt*dr*correction
                        self.hght.append(alt)
                        self.vnor.append(vn)
                        self.veas.append(ve)
                        
                        # calc vertical velocity
                        vvert = (alt-hghtold)/dt
                        #TODO check if first point is at srb

                        if vvert < 0:
                            if burst3:
                                self.has_burst = True
                                print("!!!!!! --->BURST<--- !!!!!! Alt: {0}\n".format(alt))
                            burst3 = True and burst2
                            burst2 = True and burst1
                            burst1 = True
                        else:
                            if not burst3:
                                burst1 = burst2 = False
                    
                    self.time.append(time)
                    self.lat.append(lat)
                    self.lon.append(lon)

                    latold = lat
                    lonold = lon
                    hghtold = alt
                    timeold = time
                    #print('{0} {1} {2}\n'.format(time, lat, lon))
        file.close()


    def spd_cmp(self, t1, t2):      # compares two tuples of (Vn, Ve)
        return int(math.sqrt(t1[0]*t1[0] + t1[1]*t1[1]) - math.sqrt(t2[0]*t2[0] + t2[1]*t2[1]))


    def median(self, ln, le):    # takes list of Vn and Ve, assume odd number of elements
        if ln is None or le is None:
            return None

        list = [(vn, ve) for vn, ve in zip(ln, le)]
        #print(list)
            
        sort = sorted(list, self.spd_cmp)
        length = len(sort)
        return sort[length/2];

    
    def median_filter(self):
        print("Smoothing APRS data\n")
        for i in range(1,len(self.vnor)-1):
            vn, ve = self.median(self.vnor[i-1:i+2], self.veas[i-1:i+2])
            #print("vn: {0} ve: {1}\n".format(vn, ve))
            
            self.vnor[i] = vn
            self.veas[i] = ve
            
    def get_h_and_spd(self):
        return zip(self.hght, self.vnor, self.veas)

    def get_loc(self):
        return zip(self.lat, self.lon)
    
if __name__ == "__main__":
    aprs = aprs_read()
    aprs.read_xml('aprs.xml')
    aprs.median_filter()
