import urllib.request
import urllib.error
import json
import math
import subprocess
import time

class file_context:
    def __init__(self, filename):
        self.filename = filename
        self.file = None
    def __enter__(self):
        self.file = open(self.filename, 'a')
        return self.file
    def __exit__(self, type, value, traceback):
        self.file.close()

class Realtime(object):
    def __init__(self):
        self.callsigns = ['kd8svi','kd8spq']
        self.localtime = time.localtime(time.time());
        self.time_dict = {}

        for callsign in callsigns:
            time_dict[callsign] = 0     

    def get_aprs():
        while True:
            for callsign in self.callsigns:
                APRStracking = 'http://api.aprs.fi/api/get?name={0}&what=loc&apikey=42457.M4AFa3hdkXG31&format=json'.format(callsign)
                try:
                    APRSresponse = urllib.request.urlopen(APRStracking)
                    encoding = APRSresponse.headers.get_content_charset()
                    body = APRSresponse.readall().decode(encoding)
                    
                    APRS = json.loads(body)
                    
                except urllib.error.URLError:
                    print('ERROR: Could not access APRS.fi. No internet')
                    continue
                
                print( '\n' )
                
                try:
                    for entry in APRS['entries']:
                        recTime     = entry['time']
                        latitude    = entry['lat']
                        longitude   = entry['lng']
                        altitude    = entry['altitude']
                        course	    = entry['course']
                        speed	    = entry['speed']
                except KeyError:
                    print( "entry error" )
                    continue
                
                if recTime != time_dict[callsign]:
                    print('Received packet for {0}'.format(callsign))
                    print('{0} {1} {2} {3:0.5f} {4:0.5f} {5:0.5f}'.format(recTime, latitude, longitude, float(altitude), float(course), float(speed)))
                    
                    filename = 'aprs_{0}_{1:04}_{2:02}_{3:02}.xml'.format(callsign, localtime.tm_year, localtime.tm_mon, localtime.tm_mday)
                    
                    with file_context(filename) as file:
                        file.write('<?xml version="1.0" encoding="utf-8"?>\n' )
                        file.write('<time>{0}</time><lat>{1}</lat><lng>{2}</lng><alt>{3:0.5f}'
                                   '</alt><course>{4:0.5f}</course><speed>{5:0.5f}</speed>\n'.format(recTime,
                                                                                                     latitude,
                                                                                                     longitude,
                                                                                                     float(altitude),
                                                                                                     float(course),
                                                                                                     float(speed)))
                    time_dict[callsign] = recTime
                    lastAlt  = altitude
                    yield callsign, filename
                else:
                    print('No new packets for {0}'.format(callsign))                
                    
            time.sleep(60)

API = ['46660.cVJBDcNau3YRNrO', '52288.UgFt71r5ee1Zd']

for callsign in get_aprs():
    print('Handling {0}'.format(callsign))
    # run driver with provided callsign
    pass
