from datafetch import rapid_refresh
import pprint

if __name__ == "__main__":
    rap = rapid_refresh()
    rap.read_station_list()
    filename = rap.connect_and_fetch(42.36, -86.0)
    #rap.parse_file(filename)
    
    for ind in range(len(rap.hght)):   # for every data set
        print('{0}\n'.format(rap.vnor[3][ind]))
