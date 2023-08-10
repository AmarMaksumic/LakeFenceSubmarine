import cv2
import config
import controller_listener
import controls
import logging
import start_web
import time

import _thread as thread
import tensorflow as tf
import ujson as json
import websocket as ws
import RPi.GPIO as GPIO

from cameras.camera import USBCam, Camera
from cameras import image_converter
from cameras.video_async import VideoCaptureAsync

from controls import main_controller

from multiprocessing import Process

from profiles.color_profile import ColorProfile

from websocket import create_connection

# initiate the top level logger
logging.basicConfig(
  level=logging.INFO,
  format="%(asctime)s [%(name)s] [%(levelname)-5.5s] %(message)s",
  handlers=[
    logging.StreamHandler()
  ]
)

logger = logging.getLogger('app')
# creating instance of logger object(?)

def init_pins():
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(17, GPIO.OUT) # status LED
  GPIO.setup(18, GPIO.IN) # bump sensor 1
  GPIO.setup(14, GPIO.IN) # bump sensor 2
  GPIO.setup(15, GPIO.IN) # bump sensor 3


def main():  # main method defined

  cv2.destroyAllWindows()

  init_pins()

  camera = PiCamera()
  camera.rotation = 180
  camera.resolution = (640, 480)
  camera.awb_mode = 'fluorescent'
  camera.awb_gains = 4
  camera.exposure_mode = 'off'
  rawCapture = PiRGBArray(camera, size=(640, 480))

  time.sleep(5)

  # wide_camera_ws = create_connection("ws://localhost:5805/wide_camera/ws")
  # far_camera_ws = create_connection("ws://localhost:5805/far_camera/ws")
  # processed_ws = create_connection("ws://localhost:5805/processed/ws")
  # calibration_ws = create_connection("ws://localhost:5805/calibration/ws")
  # tracking_ws = create_connection("ws://localhost:5805/tracking/ws")
  camera_ws = create_connection("ws://localhost:5805/camera/ws")
  controller_listener.start("ws://localhost:5805/dashboard/ws")

  logger.info('starting main loop ')
  frame_cnt = 0
  
  for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    test_image = frame.array
    frame_cnt += 1

    cam_jpg = image_converter.convert_to_jpg(test_image)
    camera_ws.send_binary(cam_jpg)

    cv2.waitKey(0)

  while (True):

    tracking_data = []
    ml_data = []

    frame_cnt += 1
    print(frame_cnt)
    frame_cnt_str = str(frame_cnt)
    frame_cnt_str = frame_cnt_str.zfill(4)
    print(frame_cnt_str + '.jpg')

    if main_controller.enable_camera:

      if not main_controller.enable_read_image and not cap.isOpened():
        print('opening camera')
        if main_controller.enable_dual_camera:
          farCam.open(config.far_video_source_number)
        wideCam.open(config.wide_video_source_number)
        # if the cap is not already open, do so

      if main_controller.enable_read_image:
        wide_bgr_frame = cv2.imread(frame_cnt_str + '.jpg')
      else:
        _, wide_bgr_frame = wideVideo.read()
      wide_resized_frame = cvfilters.resize(wide_bgr_frame, 640, 480)
      wide_rgb_frame = cv2.cvtColor(wide_resized_frame, cv2.COLOR_BGR2RGB)

      if main_controller.enable_dual_camera:
        _, far_bgr_frame = farVideo.read()
        far_resized_frame = cvfilters.resize(far_bgr_frame, 640, 480)
        far_rgb_frame = cv2.cvtColor(far_resized_frame, cv2.COLOR_BGR2RGB)
      else:
        far_rgb_frame = wide_rgb_frame

      if main_controller.enable_camera_feed:
        wide_jpg = image_converter.convert_to_jpg(wide_rgb_frame)
        wide_camera_ws.send_binary(wide_jpg)

        if main_controller.enable_dual_camera:
          far_jpg = image_converter.convert_to_jpg(far_rgb_frame)
          far_camera_ws.send_binary(far_jpg)

        # camera_ws.send_binary(jpg)
        # take rgb frame and convert it to a displayable jpg form, then send that as binary through websocket

      if main_controller.enable_calibration_feed:
        if main_controller.camera_mode == CAMERA_MODE_HEXAGON:
          calibration_frame = far_rgb_frame.copy()

        else:
          calibration_frame = wide_rgb_frame.copy()
        
        
        calibration_frame = color_calibrate.process(calibration_frame,
                              camera_mode=main_controller.calibration.get('camera_mode',
                                                    'RAW'),
                              color_mode=main_controller.calibration.get('color_mode'),
                              apply_mask=main_controller.calibration.get('apply_mask', False))

        jpg = image_converter.convert_to_jpg(calibration_frame)
        calibration_ws.send_binary(jpg)

      if main_controller.camera_mode == CAMERA_MODE_RAW:

        processed_frame = wide_rgb_frame
        # Camera mode set to "raw" - takes rgb frame

      elif main_controller.camera_mode == CAMERA_MODE_LOADING_BAY:

        color_profile = main_controller.color_profiles[CAMERA_MODE_LOADING_BAY]
        # Set color profile to that of "camera mode loading bay"
      
        ml_data = ml.predict(wide_rgb_frame, interpreter, input_details, output_details)

        tracking_data = bay_tracker.process(wide_rgb_frame,
                                            camera,
                                            frame_cnt,
                                            color_profile)
        # Frame is displayed with bay tracking properties

      elif main_controller.camera_mode == CAMERA_MODE_BALL:

        color_profile = main_controller.color_profiles[
          CAMERA_MODE_BALL]  # color profile set to the CAMERA MODE BALL one
        # print("ball")

        ml_data = ml.predict(wide_rgb_frame, interpreter, input_details, output_details)

        tracking_data = ball_tracker2.process(wide_rgb_frame,
                                              camera,
                                              frame_cnt,
                                              color_profile)

        processed_frame, tracking_data = ball_tracker2.combine(wide_rgb_frame,
                                                                tracking_data,
                                                                ml_data,
                                                                15)


      elif main_controller.camera_mode == CAMERA_MODE_HEXAGON:

        color_profile_hex = main_controller.color_profiles[CAMERA_MODE_HEXAGON]
        
        ml_data = ml.predict(far_rgb_frame, interpreter, input_details, output_details)

        tracking_data_port = port_tracker.process(far_rgb_frame,
                                              camera,
                                              frame_cnt,
                                              color_profile_hex)
        
        processed_frame, tracking_data = port_tracker.combine(far_rgb_frame,
                                                                tracking_data_port,
                                                                ml_data,
                                                                15)
      

      if main_controller.enable_processing_feed:  # once we start showing our processing feed...

        cv2.putText(processed_frame,
              'Tracking Mode %s' % main_controller.camera_mode,
              (10, 10),
              cv2.FONT_HERSHEY_DUPLEX,
              .4,
              colors.BLUE,
              1,
              cv2.LINE_AA)

        jpg = image_converter.convert_to_jpg(processed_frame)
        processed_ws.send_binary(jpg)

        # if out is not None:
        #     out.write(frame)
      if len(tracking_data) != 0 and main_controller.send_tracking_data:
        # sort tracking data by closests object
        # logger.info(tracking_data)
        tracking_data = sorted(tracking_data, key=lambda i: i['dist'])
        tracking_ws.send(json.dumps(dict(targets=tracking_data)))

      # cv2.imshow('frame', processed_frame )
      # cv2.waitKey(0)

    else:
      logger.info('waiting for control socket')
      # IDLE mode
      if not main_controller.enable_read_image and cap.isOpened():
        print('closing camera')
        wideCam.stop()
        if main_controller.enable_dual_camera:
          farCam.stop()
      time.sleep(.3)

    cv2.waitKey(0)

    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break


if __name__ == '__main__':
  p = Process(target=start_web.main)
  p.start()
  main()
  p.join()
