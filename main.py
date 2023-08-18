import gpiozero
import RPi.GPIO as GPIO
import cv2
import time
import socket
from picamera.array import PiRGBArray
from picamera import PiCamera
from multiprocessing import Process
from threading import Thread
import _thread
import threading
import pickle
import select
import struct
# import start_web

def listener(client, address):
  print("Accepted connection from: ", address)
  with clients_lock:
    clients.add(client)
  try:    
    while True:
      data = client.recv(1024)
      if data == '0':
        timestamp = datetime.datetime.now().strftime("%I:%M:%S %p")
        client.send(timestamp)
        time.sleep(2)
  finally:
    with clients_lock:
      clients.remove(client)
      client.close()

clients = set()
clients_lock = threading.Lock()
host = "192.168.0.193"


port = 10016

s = socket.socket()
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((host,port))
s.listen(6)
read_list = [s]
th = []

def input():
  send_str = 'thank you'
  pump_stat, arm_stat, prop_x, prop_y = 0, 0, 0, 0
   
  while True:
    time.sleep(0.05)
    try:
      readable, writable, errored = select.select(read_list, [], [], 1)
      for x in readable:
        if x is s:
          client_socket, address = s.accept()
          read_list.append(client_socket)
          print("[1] Connection from", address)
        else:
          data = x.recv(1024).decode('utf-8')
          if len(data) > 1 and data[0] == '6':
            # get
            pump_stat = int(data[1])
            arm_stat = int(data[2])
            prop_x = int(data[3:-4])
            prop_y = int(data[7:])
            # print(pump_stat, " ", arm_stat, " ", prop_x, " ", prop_y)
            if pump_stat == 0: print('Pump expelling')
            elif pump_stat == 1: print('Pump locked')
            elif pump_stat == 2: print('Pump compressing')
            if arm_stat == 0: print('Arm retracting')
            elif arm_stat == 1: print('Arm locked')
            elif arm_stat == 2: print('Arm extending')
            print('Motor X In: ', prop_x)
            print('Adjusted to serial send: b\'', (prop_x-512)/4, '\'')
            print('Motor Y In: ', prop_y)
            print('Adjusted to serial send: b\'', (prop_y-512)/4, '\'')
            x.sendall(send_str.encode('utf-8'))
          else:
            x.close()
            read_list.remove(x)
    except:
      print("aop")

def ultras():

  print("starting ultras")

  TRIG_1 = 23
  ECHO_1 = 24
  TRIG_2 = 27
  ECHO_2 = 22

  GPIO.setup(TRIG_1, GPIO.OUT) # bump sensor 1 trig
  GPIO.setup(ECHO_1, GPIO.IN) # bump sensor 1 echo
  GPIO.output(TRIG_1, False)
  GPIO.setup(TRIG_2, GPIO.OUT) # bump sensor 2 trig
  GPIO.setup(ECHO_2, GPIO.IN) # bump sensor 2 echo
  GPIO.output(TRIG_2, False)

  time.sleep(2)
  while (True):
    # client, address = s.accept()

    #bump 1
    GPIO.output(TRIG_1, True)

    time.sleep(0.00001)

    GPIO.output(TRIG_1, False)

    pulse_start, pulse_end = 0, 0
    crashed = time.time()

    while GPIO.input(ECHO_1) == 0:
      pulse_start = time.time()
      if (time.time() - crashed > 0.1):
        ultras()

    crashed = time.time()
    while GPIO.input(ECHO_1) == 1:
      pulse_end = time.time()
      if (time.time() - crashed > 0.1):
        ultras()

    pulse_duration = pulse_end - pulse_start

    distance = pulse_duration * 17150

    distance1 = round(distance, 2)

    time.sleep(0.1)

    #bump 2
    GPIO.output(TRIG_2, True)

    time.sleep(0.00001)

    GPIO.output(TRIG_2, False)

    pulse_start, pulse_end = 0, 0
    crashed = time.time()

    while GPIO.input(ECHO_2) == 0:
      pulse_start = time.time()
      if (time.time() - crashed > 0.1):
        ultras()

    crashed = time.time()
    while GPIO.input(ECHO_2) == 1:
      pulse_end = time.time()
      if (time.time() - crashed > 0.1):
        ultras()

    pulse_duration = pulse_end - pulse_start

    distance = pulse_duration * 17150

    distance2 = round(distance, 2)

    time.sleep(0.1)

    print("BUMP1: ", distance1, "cm ===> BUMP2: ", distance2, "cm")
    send_str = "BUMP1: " + str(distance1) + "cm ===> BUMP2: " + str(distance2) + "cm"
    try:
      readable, writable, errored = select.select(read_list, [], [], 1)
      for x in readable:
        if x is s:
          client_socket, address = s.accept()
          read_list.append(client_socket)
          print("[2] Connection from", address)
        else:
          data = x.recv(1024).decode('utf-8')
          if data == '0':
            x.sendall(send_str.encode('utf-8'))
          else:
            x.close()
            read_list.remove(x)
    except:
      print("woop")
  s.close()

def cam():

  print("running camera")
  camera = PiCamera()
  camera.rotation = 180
  camera.resolution = (640, 480)
  # camera.awb_mode = 'fluorescent'
  # camera.awb_gains = 4
  # camera.exposure_mode = 'off'
  rawCapture = PiRGBArray(camera, size=(640, 480))
  time.sleep(0.1)
  for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    test_image = frame.array
    cv2.imshow('image', test_image)
    send_str = pickle.dumps(test_image)
    try:
      readable, writable, errored = select.select(read_list, [], [], 1)
      for x in readable:
        if x is s:
          client_socket, address = s.accept()
          read_list.append(client_socket)
          print("[3] Connection from", address)
        else:
          data = x.recv(1024).decode('utf-8')
          if data == '1':
            x.sendall(struct.pack("L", len(send_str)) + send_str)
          else:
            x.close()
            read_list.remove(x)
    except:
      print("oopsies")
    key = cv2.waitKey(1) & 0xFF

    rawCapture.truncate(0)

    if key == ord("q"):
      GPIO.cleanup()
      break

 
if __name__ == "__main__":
  GPIO.cleanup()
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  p1 = Process(target=ultras)
  p2 = Process(target=cam)
  p3 = Process(target=input)

  p1.start()
  p2.start()
  p3.start()

  p1.join()
  p2.join()
  p3.join()
  # ultras()