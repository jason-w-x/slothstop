import json
import socket
import signal
import sys
from threading import Thread
from multiprocessing import Process
from rt.aprs import APRSIS
from rt.APRSparse import fetch_and_write
from rt.runreal import runreal_wrapper

def signal_handler(signal,frame):
    sys.exit(0)

def start_real_time(*args,**kwargs):
    print("func called with args {0}\n".format(kwargs))
    callsign = kwargs[u'callsign']
    t1 = Thread(target=fetch_and_write,args=(callsign,))
    t1.start()

    t2 = Thread(target=runreal_wrapper, kwargs=kwargs)
    t2.start()
    print('called fetch_and_write')

def handle_req(*args, **kwargs):
    clientsock = args[0]
    addr = args[1]

    msg = json.loads(clientsock.recv(1028))
	
    # send ack
    clientsock.send("received thnx")
    clientsock.close()

    # msg will be name of fn + kwargs
    # convert to callable, call

    name = msg[0]
    kws = msg[1]
    
    func = globals()[name]
    func(**kws)    

def listen():
    host = "127.0.0.1"
    port = 50001

    sock = socket.socket()

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind((host,port))
    sock.listen(1)

    while(True):
        try:
            (clientsock, addr) = sock.accept()
        except:
            continue

        req_process = Process(target=handle_req,args=((clientsock,addr)))
		req_process.start()
        
if __name__ == "__main__":
    # setup stuff? if necessary

    signal.signal(signal.SIGINT, signal_handler)

    listen()
