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
        self.wspd = []  # wind speed (m/s)

    def read_xml(self, filename):
        file = open(filename, 'r')

        timeold = 0.0
        hghtold = None
        latold  = None
        lonold  = None

        burst1 = False
        burst2 = False
        burst3 = False
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
                        self.vnor.append((lat-latold)/dt*dr)
                        self.veas.append((lon-lonold)/dt*dr*correction)

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
                    print('{0} {1} {2}\n'.format(time, lat, lon))

                    #Port from driver.pl
        file.close()


if __name__ == "__main__":
    aprs = aprs_read()
    aprs.read_xml('aprs.xml')
