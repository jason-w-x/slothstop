import urllib2
import json
import math
import time

callsign = raw_input('Enter callsign to track: ')

API = ['46660.cVJBDcNau3YRNrO', '52288.UgFt71r5ee1Zd']

#APRStracking = 'http://api.aprs.fi/api/get?name=' + callsign + '&what=loc&apikey=42457.M4AFa3hdkXG31&format=json'

localtime = time.localtime(time.time());

fileName = 'aprs.xml'

print( fileName )

APRSfile = open( fileName, 'a' )
APRSfile.close()

lastTime = 0
lastAlt  = 0

while( 1 ):
	for key in API:
		print(key)
		print("\n")
		APRStracking = 'http://api.aprs.fi/api/get?name=' + callsign + '&what=loc&apikey=' + key + '&format=json'
		try:
			APRSresponse = urllib2.urlopen( APRStracking )
			body = APRSresponse.read()
			
			APRS = json.loads( body )
			
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
		except KeyError:
			print( "entry error" )
			time.sleep(60)
			continue
		
		print( '\n' )
		
		if( recTime != lastTime ):
			#Vn = float(speed) * math.sin((270.0-float(course))*(3.141592/180));
			#Ve = float(speed) * math.cos((270.0-float(course))*(3.141592/180));
			print( "Received packet" )
			print( '{0} {1} {2} {3}\n'.format(recTime,latitude,longitude,altitude))
			
			APRSfile = open( fileName, 'a' )
			APRSfile.write( '{0} {1} {2} {3}\n'.format(recTime,latitude,longitude,altitude))
			APRSfile.close()
		else:
			print( "No new packets" )
			
		lastTime = recTime
		lastAlt  = altitude
		
		time.sleep(60)

APRSfile.close()
