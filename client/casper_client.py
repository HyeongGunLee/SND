# -*- coding: utf-8 -*-

import os
import socket
import picamera
import cv2
import numpy
import urllib.request
import pygame
import RPi.GPIO as GPIO
import time
import datetime


os.system("sudo modprobe bcm2835-v4l2")
os.system("sudo rdate -s time.bora.net")

object_button = 17
text_button = 25
time_button = 16
trig = 13
echo = 27

HOST = "164.125.35.41"
PORT = 1107


def set_GPIO():
	GPIO.setmode(GPIO.BCM)

	GPIO.setup(object_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(text_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup(time_button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

	GPIO.setup(trig, GPIO.OUT)
	GPIO.setup(echo, GPIO.IN)


def send_image(flag):
	camera.capture('image.jpg')
	frame = cv2.imread('image.jpg')

	encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
	result, img_encode = cv2.imencode('.jpg', frame, encode_param)
	data = numpy.array(img_encode)
	string_data = data.tostring()

	socket.send(flag.encode())
	socket.send(bytes(str(len(string_data)).ljust(16), 'utf-8'))
	socket.send(bytes(string_data))


def get_distance():
	GPIO.output(trig, True)
	time.sleep(0.00001)
	GPIO.output(trig, False)

	while (GPIO.input(echo) == 0):
		pulse_start = time.time()
	while (GPIO.input(echo) == 1):
		pulse_end = time.time()
	pulse_duration = pulse_end - pulse_start
	distance = pulse_duration * 17000
	distance = round(distance, 2)

	return distance


def naver_TTS(text):
	client_id = "PIRJyxr5CxA1zX0TgBw1"
	client_secret = "1sNTA9RAtI"
	encText = urllib.parse.quote(text)
	data = "speaker=jinho&speed=-2&text=" + encText
	url = "https://openapi.naver.com/v1/voice/tts.bin"
	request = urllib.request.Request(url)
	request.add_header("X-Naver-Client-Id", client_id)
	request.add_header("X-Naver-Client-Secret", client_secret)
	response = urllib.request.urlopen(request, data=data.encode('utf-8'))
	rescode = response.getcode()
	if (rescode == 200):
		response_body = response.read()
		with open('tts.mp3', 'wb') as f:
			f.write(response_body)
			pygame.mixer.init()
			pygame.mixer.music.load('tts.mp3')
			pygame.mixer.music.play()
	else:
		print("Error Code: " + rescode)


try:
	socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	socket.connect((HOST, PORT))

	camera = picamera.PiCamera()
	set_GPIO()

	while True:
		if (GPIO.input(object_button) == 0):
			flag = 'object'
			send_image(flag)
			distance = get_distance()
			foot = int(distance / 30) + 1
			result = socket.recv(1024).decode()
			text = result + "는 " + str(foot) + "걸음 앞에 있습니다."
			naver_TTS(text)
			
		elif (GPIO.input(text_button) == 0):
			flag = 'text'
			send_image(flag)
			result = socket.recv(4096).decode()
			naver_TTS(result)
			
		elif (GPIO.input(time_button) == 0):
			now = datetime.datetime.now()
			hour = now.strftime('%H')
			minute = now.strftime('%M')
			text = "현재 시각은 " + str(hour) + "시 " + str(minute) + "분 입니다."
			naver_TTS(text)

finally:
	socket.close()
	GPIO.cleanup()
