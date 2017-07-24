# -*- coding: utf-8 -*-

#import os
import cv2
import socket
import numpy
import pygame
import urllib.request

HOST = '127.0.0.1'
PORT = 1107

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

#os.system('sudo modprobe bcm2835-v4l2')

client_id = "PIRJyxr5CxA1zX0TgBw1"
client_secret = "1sNTA9RAtI"

def naver_tts(text):
    encText = urllib.parse.quote(text)
    data = "speaker=mijin&speed=0&text=" + encText
    url = "https://openapi.naver.com/v1/voice/tts.bin"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    response = urllib.request.urlopen(request, data=data.encode('utf-8'))
    rescode = response.getcode()
    if (rescode == 200):
        print("TTS mp3")
        response_body = response.read()
        with open('tts.mp3', 'wb') as f:
            f.write(response_body)
            pygame.mixer.init()
            pygame.mixer.music.load('tts.mp3')
            pygame.mixer.music.play()
    else:
        print("Error Code: " + rescode)


try:
    capture = cv2.VideoCapture(0)
    ret, frame = capture.read()

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    result, img_encode = cv2.imencode('.jpg', frame, encode_param)
    data = numpy.array(img_encode)
    string_data = data.tostring()



    s.send(bytes(str(len(string_data)).ljust(16), 'utf-8'))
    s.send(bytes(string_data))

    x = s.recv(1024).decode()
    print('server : ' + x)
    naver_tts(x)


    cv2.imshow('client', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

finally:
    s.close()