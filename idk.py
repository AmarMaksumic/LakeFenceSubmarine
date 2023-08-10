import gpiozero
import RPi.GPIO as GPIO
from picamera.array import PiRGBArray
from picamera import PiCamera
from multiprocessing import Process

import start_web

def init_pins():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(17, GPIO.OUT) # status LED
  GPIO.setup(18, GPIO.IN) # bump sensor 1
  GPIO.setup(14, GPIO.IN) # bump sensor 2
  GPIO.setup(15, GPIO.IN) # bump sensor 3


def main():
  print("Running main.py")
  camera = PiCamera()
  camera.rotation = 180
  camera.resolution = (640, 480)
  camera.awb_mode = 'fluorescent'
  camera.awb_gains = 4
  camera.exposure_mode = 'off'
  rawCapture = PiRGBArray(camera, size=(640, 480))
  time.sleep(0.1)
  for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    test_image = frame.array


if __name__ == "__main__":
  p1 = Process(target=start_web.main)
  p2 = Process(target=main)

  p1.start()
  p2.start()

  p1.join()
  p2.join()