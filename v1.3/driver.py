from datafetch import rapid_refresh
import pprint

if __name__ == "__main__":
    rap = rapid_refresh()
    filename = rap.connect_and_fetch()
    rap.parse_file(filename)
    
    for ind in range(len(rap.hght)):   # for every data set
        print(rap.temp[ind])
