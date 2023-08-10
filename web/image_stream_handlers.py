from os.path import abspath, dirname, join
import numpy as np

import json
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler, WebSocketClosedError

import threading

import time
import asyncio
import logging

import tornado.ioloop
import tornado.web
import tornado.websocket

import logging
import time

logger = logging.getLogger('imagestream')
import uuid

import cv2
from PIL import Image
from io import BytesIO
from processing import colors
from processing import cvfilters

# not part of calibration anymore
def convert_to_jpg(image):
    """TBW."""
    im = Image.fromarray(image)
    mem_file = BytesIO()
    im.save(mem_file, 'JPEG')
    return mem_file.getvalue()

class CameraFeedHandler(tornado.websocket.WebSocketHandler):
    """
    """
    watchers = set()
    def open(self):
        self.uid = str(uuid.uuid4())
        logger.info("CameraFeedHandler websocket opened %s" % self.uid)
        CameraFeedHandler.watchers.add(self)

    def check_origin(self, origin):
        """
            Allow CORS requests
        """
        return True

    """
    broadcast to clients, assumes its target data
    """
    def on_message(self, message):
        # logger.info('pushing image')
        for waiter in CameraFeedHandler.watchers:
            if waiter == self:
                continue
            waiter.write_message(message, binary=True)

    def send_msg(self, msg):
        try:
            self.write_message(msg, False)
        except WebSocketClosedError:
            logger.warn("websocket closed when sending message")

    def on_close(self):
        logger.info("image websocket closed %s" % self.uid)
        CameraFeedHandler.watchers.remove(self)


class ImageStreamHandler(tornado.websocket.WebSocketHandler):
    """TBW."""

    def __init__(self, *args, **kwargs):
        """TBW."""
        self.counter = 0
        super().__init__(*args, **kwargs)

    def on_connection_close(self):
        """TBW."""
        self.close()

    @staticmethod
    def start(application):
        """TBW."""
        pass  # unused, for API compatibility with ImagePushStreamHandler

    @staticmethod
    def stop():
        """TBW."""
        pass  # unused, for API compatibility with ImagePushStreamHandler

    async def on_message(self, message):
        """TBW."""
        self.counter += 1
        try:
            if message == '?':
                image = self.application.settings['camera'].read_image()
                await self.write_message(image, binary=True)
            else:
                await self.write_message(message)  # echo
        except Exception as exc:
            logger.exception(exc)


class ImagePushStreamHandler(tornado.websocket.WebSocketHandler):
    """TBW."""

    # images = []  # type: t.List[ImagePushStreamHandler]
    interval = 1
    stop_event = threading.Event()

    camera_mode = 'RAW'
    color_mode = None
    apply_mask = False

    def __init__(self, *args, **kwargs):
        """TBW."""
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.camera_mode = 'RAW'
        self.images = []
        self._periodic = tornado.ioloop.PeriodicCallback(self._write_queue, 40)
        self._periodic.start()
        self.application.settings['sockets'].append(self)

    def on_connection_close(self):
        """TBW."""
        logger.info('Closing web socket...')
        self.close()
        self._periodic.stop()
        try:
            self.application.settings['sockets'].remove(self)
        except ValueError:
            pass

    @staticmethod
    def start(application):
        """TBW."""
        th = threading.Thread(target=ImagePushStreamHandler.read_image_loop,
                              args=(application,),
                              name='read-camera')
        th.start()

    @staticmethod
    def stop():
        """TBW."""
        ImagePushStreamHandler.stop_event.set()

    @staticmethod
    def read_image_loop(application):
        """TBW."""
        cam = application.settings['camera']
        while not ImagePushStreamHandler.stop_event.is_set():
            interval = float(ImagePushStreamHandler.interval) / 1000.0
            if interval > 0:
                if len(application.settings['sockets']):
                    _, image = cam.read()

                    image = cv2.resize(image, ((int)(640), (int)(400)), 0, 0, cv2.INTER_CUBIC)
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)



                    if ImagePushStreamHandler.camera_mode != 'RAW':



                        color_profile = application.settings['color_profiles'].get(ImagePushStreamHandler.camera_mode)

                        mask = None


                        if ImagePushStreamHandler.color_mode == 'rgb':
                            mask = cv2.inRange(image,
                                               (color_profile.red.min, color_profile.green.min, color_profile.blue.min),
                                               (color_profile.red.max, color_profile.green.max, color_profile.blue.max))

                        elif ImagePushStreamHandler.color_mode == 'hsv':
                            hue = color_profile.hsv_hue
                            sat = color_profile.hsv_sat
                            val = color_profile.hsv_val

                            hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
                            mask = cv2.inRange(hsv, (hue.min, sat.min, val.min),  (hue.max, sat.max, val.max))
                        #
                        # elif ImagePushStreamHandler.color_mode == 'hsl':
                        #     hue = color_profile.hsl_lum
                        #     sat = color_profile.hsl_lum
                        #     lum = color_profile.hsl_lum
                        #     hsl = cv2.cvtColor(image, cv2.COLOR_BGR2HSL)
                        #     hsl = cv2.inRange(image, (hue.min, sat.min, lum.min),  (hue.max, sat.max, lum.max))

                        if mask is not None:
                            if ImagePushStreamHandler.apply_mask:
                                image = cvfilters.apply_mask(image, mask)
                                image = cv2.erode(image, None, iterations=2)
                                image = cv2.dilate(image, None, iterations=2)
                            else:
                                image = mask

                    cv2.putText(image,
                            'Mode %s' % ImagePushStreamHandler.camera_mode,
                            (20,20),
                            cv2.FONT_HERSHEY_DUPLEX,
                            .4,
                            colors.BLUE,
                            1,
                            cv2.LINE_AA)

                    if ImagePushStreamHandler.color_mode is not None:
                        cv2.putText(image,
                                    'COLOR Mode %s' % ImagePushStreamHandler.color_mode,
                                    (20,40),
                                    cv2.FONT_HERSHEY_DUPLEX,
                                    .4,
                                    colors.BLUE,
                                    1,
                                    cv2.LINE_AA)
                    jpg = convert_to_jpg(image)
                    for ws in application.settings['sockets']:
                        ws.images.append(jpg)

                interval = 0.001
            else:
                interval = 1.0  # paused
            time.sleep(interval)
        logger.info('Exiting ImagePushStreamHandler.read_image_loop')

    async def _write_queue(self):
        """TBW."""
        for _ in range(50):
            if self.images:
                break
            await asyncio.sleep(0.001)

        while self.images:
            image = self.images.pop()
            self.images.clear()
            try:
                await self.write_message(image, binary=True)
            except tornado.websocket.WebSocketClosedError:
                self.close()
                socks = self.application.settings['sockets']
                if self in socks:
                    socks.remove(self)

    async def on_message(self, message):
        """TBW."""
        self.counter += 1
        try:
            if message == '?':
                await self._write_queue()
            elif message.startswith('interval'):
                interval = int(message.split('=')[-1])
                self._periodic = interval
                ImagePushStreamHandler.interval = interval
                # self.write_message(message)  # echo

            else:
                logger.info('IN ' + message)
                profile = json.loads(message)
                ImagePushStreamHandler.camera_mode = profile['camera_mode']
                ImagePushStreamHandler.color_mode = profile['color_mode']
                ImagePushStreamHandler.apply_mask = profile['apply_mask']

        except Exception as exc:
            logger.exception(exc)