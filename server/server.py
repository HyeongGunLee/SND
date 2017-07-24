# -*- coding: utf-8 -*-

import cv2
import socket
import numpy

HOST = ''
PORT = 1107

def recval(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()

try:
    length = recval(conn, 16)
    string_data = recval(conn, int(length))
    data = numpy.fromstring(string_data, dtype='uint8')

    x = 'cup'
    conn.send(x.encode())

    dec_img = cv2.imdecode(data, 1)
    cv2.imshow('server', dec_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    conn.close()

finally:
    s.close()