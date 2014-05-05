from driver import driver
from getpass import getpass
from subprocess import Popen, PIPE
from time import sleep
from util import get_time_suffix
import os, shutil, signal

callsigns = ['kd8tmy-11', 'kd8cjt']

def signal_handler(signum, frame):
    print('Destroying Kerberos auth\n')
    args = ('kdestroy')
    popen = Popen(args).wait()
    exit()

def setup_kerb_auth():
    print('Setting up Kerberos auth\n')
    args = ('kinit')
    popen = Popen(args, stdin=PIPE)
    pw = getpass('')
    popen.communicate(pw)
    
def setup_index_file():
    file = open('index.html', 'w')
    file.write('<!DOCTYPE html>\n')
    file.write('<html>\n')
    file.write('\t<body>\n')
    for callsign in callsigns:
        file.write('\t\t<a href=\"{0}.html\">{0}</a>\n'.format(callsign))
    file.write('\t</body>\n')
    file.write('</html>\n')
    file.close()

    args = ('scp', 'index.html', 'jasonx@sftp.itcs.umich.edu:Public/html/')
    popen = Popen(args).wait()
    os.remove('index.html')
    
if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    
    # lets us ssh/scp files without typing in a pw every time
    setup_kerb_auth()

    dir_name = get_time_suffix()
    
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    #setup_index_file()

    counter = 0
    while True:
        for callsign in callsigns:
            print('Handling {0}\n'.format(callsign))
            aprsfile = 'aprs_{0}_{1}.xml'.format(callsign, dir_name)
            print(aprsfile)
            driver(callsign, 7.11, 2000, 1.5, 6, aprsfile, 42.3122, -85.2042)

            new_file_dir = '{0}/{1}{2:02d}.html'.format(dir_name,
                                                        callsign,
                                                        counter)
            shutil.copyfile('index.html', new_file_dir)

            print('Pushing {0}.html to caen\n'.format(callsign))
            args = ('scp', 'index.html', 'jasonx@sftp.itcs.umich.edu:Public/html/{0}RAP.html'.format(callsign))
            popen = Popen(args).wait()
            
        sleep(120)
            
        counter += 1
