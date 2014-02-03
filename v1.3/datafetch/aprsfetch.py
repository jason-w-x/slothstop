import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind(('www.aprs2.net',14580))


