from datafetch import rapid_refresh, aprs_read
from subprocess import Popen, PIPE

def merge_data(rap, aprs, time):
    lastdat = 0.0
    for idx, (h, p, t, n, e) in enumerate(rap.data[time]):        
        avn = [vn for (ht, vn, ve) in aprs.get_h_and_spd() if ht > lastdat and ht < h]
        ave = [ve for (ht, vn, ve) in aprs.get_h_and_spd() if ht > lastdat and ht < h]
        
        if avn and ave:
            vn = sum(avn)/len(avn)
            ve = sum(ave)/len(avn)
            rap.data[time][idx] = (h, p, t, vn, ve)
            
        lastdat = h
    
def write_data(rap, aprs, callsign, time):
    filename = "RAP{0}".format(callsign)
    out = open(filename, 'w')
    
    out.write("42.09619 -84.89647 {0}\n".format(rap.elev))   # data location
    out.write("{0}\n".format(len(rap.data[time])))           # number of weather data pts
    for (h, p, t, n, e) in rap.data[time]:
        out.write("{0} {1} {2} {3} {4}\n".format(p, h, t, e, n))

    out.write("{0} {1} {2}\n".format(aprs.lat[-1] if aprs.lat else rap.lat,
                                     aprs.lon[-1]-360.0 if aprs.lon else rap.lon,
                                     aprs.hght[-1] if aprs.hght else rap.elev))  # curr loc
    
    out.write("{0}\n".format(int(aprs.has_burst)))
    out.write("0\n")   # force burst
    out.write("{0}\n".format(len(aprs.lat)))   # number of APRS points

    for (lat, lon) in aprs.get_loc():
        out.write("{0} {1}\n".format(lat, lon-360.0))

    out.close()
    return filename

  
# drives a single prediction using RAP model data and APRS points
#   mass    - mass of payload (lbs)
#   balloon - balloon mass (grams)
#   tanks   - tanks of helium (float)
#   para    - diameter of parachute (ft)
#   time    - time in the future (hr)

def driver(callsign, mass, balloon, tanks, para, aprsfile, lat, lon, time=0):
    rap = rapid_refresh()
    filename = rap.connect_and_fetch(lat, lon)
    rap.parse_file(filename)
        
    aprs = aprs_read()
    aprs.read_xml(aprsfile)   # parses and converts APRS values
    aprs.median_filter()

    # overwrite weather data with APRS data
    merge_data(rap, aprs, time)
    
    # write hybrid data to file
    filename = write_data(rap, aprs, callsign, time)

    # runs C preds with provided vals
    args = ('./run', filename)
    popen = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    pred_input = '{0}\r{1}\r{2}\r{3}\r'.format(mass, balloon, tanks, para)
    out, err = popen.communicate(pred_input)
    print(out)
    

if __name__ == "__main__":
    driver(7.11, 2000, 1.5, 6, 'temp.xml', 42.312, -85.204, 3)
