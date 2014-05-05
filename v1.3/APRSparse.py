import urllib2
#import urllib.request
#import urllib.error
import json
import math
import time

callsign = raw_input('Enter callsign to track: ')

API = ['46660.cVJBDcNau3YRNrO', '52288.UgFt71r5ee1Zd']

#APRStracking = 'http://api.aprs.fi/api/get?name=' + callsign + '&what=loc&apikey=42457.M4AFa3hdkXG31&format=json'

localtime = time.localtime(time.time());
 
fileName = 'aprs_' + callsign + '_%04d_%02d_%2d' % ( localtime[0], localtime[1], localtime[2] ) + '.xml'

print( fileName )

APRSfile = open( fileName, 'a' )
APRSfile.close()

lastTime = 0
lastAlt  = 0

while True:
    for key in API:
        print(key)
        print('\n')
        APRStracking = 'http://api.aprs.fi/api/get?name=' + callsign + '&what=loc&apikey=' + key + '&format=json'
        try:
            #APRSresponse = urllib.request.urlopen( APRStracking )
            APRSresponse = urllib2.urlopen(APRStracking)
			#encoding = APRSresponse.headers.get_content_charset()
			#body = APRSresponse.readall().decode( encoding )
            body = APRSresponse.read()
            APRS = json.loads( body )
			
		#except urllib.error.URLError:
        except urllib2.URLError:
            print( "ERROR: Could not access APRS.fi. No internet" )
            continue
			
        print( '\n' )
		
        try:
            for entry in APRS['entries']:
                recTime	 	= entry['time']
                latitude 	= entry['lat']
                longitude	= entry['lng']
                altitude	= entry['altitude']
                course      = 0
                speed       = 0
                #course		= entry['course']
                #speed		= entry['speed']
        except KeyError:
            print( "entry error" )
            time.sleep(60)
            continue
		
        print( '\n' )
		
        if( recTime != lastTime ):
			#Vn = float(speed) * math.sin((270.0-float(course))*(3.141592/180));
			#Ve = float(speed) * math.cos((270.0-float(course))*(3.141592/180));
            print( "Received packet" )
            print( recTime + ' ' + latitude + ' ' + longitude + ' %.5f %.5f %.5f' % ( float(altitude), float(course), float(speed) ) )#% (course) % (speed)
			
            APRSfile = open( fileName, 'a' )	
            APRSfile.write( '<?xml version="1.0" encoding="utf-8"?>\n' )
            APRSfile.write( '<time>' + recTime + '</time><lat>' + latitude + '</lat><lng>' + longitude + '</lng>' )
            APRSfile.write( '<alt>%.5f</alt><course>%.5f</course><speed>%.5f</speed>\n' % ( float(altitude), float(course), float(speed)  ) )
            APRSfile.close()
        else:
            print( "No new packets" )
			
        lastTime = recTime
        lastAlt  = altitude
			
        time.sleep(60)

APRSfile.close()
