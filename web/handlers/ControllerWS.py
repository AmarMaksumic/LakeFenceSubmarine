from os.path import abspath, dirname, join

import uuid
import logging
import time
import json
import json as json_encode

from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler, WebSocketClosedError

from controls import main_controller
from profiles.color_profile import ColorProfileEncoder

logger = logging.getLogger(__name__)

root_path = abspath(join(dirname(__file__),"../../"))

class ControllerWS(WebSocketHandler):
    """
           A tornado web handler that forwards values between NetworkTables
           and a webpage via a websocket
       """

    watchers = set()
    def open(self):
        self.uid = str(uuid.uuid4())
        logger.info("Controller websocket opened")
        self.write_message('connected')
        ControllerWS.watchers.add(self)

        self.ioloop = IOLoop.current()
        self.write_message(json_encode.dumps(dict(socket=self.uid,
                                                  enable_camera_feed=main_controller.enable_camera_feed,
                                                  enable_processing_feed=main_controller.enable_processing_feed,
                                                  enable_calibration_feed= main_controller.enable_calibration_feed,
                                                  color_profiles=self.application.settings['color_profiles']),
                                                  cls=ColorProfileEncoder))

    def check_origin(self, origin):
        """
            Allow CORS requests
        """
        return True

    def on_message(self, message):

        logger.info(message)
        controls = json.loads(message)

        if 'request_type' in controls:

            if controls['request_type'] == 'calibration':
                main_controller.calibration = controls


        if 'controls' in controls:

            if 'camera_mode' in controls['controls']:
                main_controller.camera_mode = controls['controls']['camera_mode']


        if 'enable_calibration_feed' in controls:
            main_controller.enable_calibration_feed = controls['enable_calibration_feed']

        if 'enable_camera_feed' in controls:
            main_controller.enable_camera_feed = controls['enable_camera_feed']

        if 'enable_processing_feed' in controls:
            main_controller.enable_processing_feed = controls['enable_processing_feed']

        if 'color_profiles' in controls:
            for (camera_mode, profile ) in controls['color_profiles'].items():
                logger.info('updating %s ' % camera_mode)
                current_profile = main_controller.color_profiles.get(camera_mode)
                current_profile.update(profile)

        if 'color_profile' in controls:
            profile = controls['color_profile']
            logger.info('updating %s ' % profile['camera_mode'])
            current_profile = main_controller.color_profiles.get(profile['camera_mode'])
            current_profile.update(profile)


            # color_profile = self.application.settings['color_profiles'].get(profile['camera_mode'])
            # logger.info('updating color profile for %s' % color_profile.camera_mode)
            #
            # color_profile.red.min = int(profile['rgb']['r']['min'])
            # color_profile.red.max = int(profile['rgb']['r']['max'])
            #
            # color_profile.green.min = int(profile['rgb']['g']['min'])
            # color_profile.green.max = int(profile['rgb']['g']['max'])
            #
            # color_profile.blue.min = int(profile['rgb']['b']['min'])
            # color_profile.blue.max = int(profile['rgb']['b']['max'])
            #
            # color_profile.hsv_hue.min = int(profile['hsv']['h']['min'])
            # color_profile.hsv_hue.max = int(profile['hsv']['h']['max'])
            #
            # color_profile.hsv_sat.min = int(profile['hsv']['s']['min'])
            # color_profile.hsv_sat.max = int(profile['hsv']['s']['max'])
            #
            # color_profile.hsv_val.min = int(profile['hsv']['v']['min'])
            # color_profile.hsv_val.max = int(profile['hsv']['v']['max'])
            #
            # color_profile.hsl_hue.min = int(profile['hsl']['h']['min'])
            # color_profile.hsl_hue.max = int(profile['hsl']['h']['max'])
            #
            # color_profile.hsl_sat.min = int(profile['hsl']['s']['min'])
            # color_profile.hsl_sat.max = int(profile['hsl']['s']['max'])
            #
            # color_profile.hsl_lum.min = int(profile['hsl']['l']['min'])
            # color_profile.hsl_lum.max = int(profile['hsl']['l']['max'])

            if 'reset' in controls:
                self.write_message(json_encode.dumps(dict(socket=self.uid,
                                                      color_profiles=self.application.settings['color_profiles']),
                                                      cls=ColorProfileEncoder))

            if 'save' in controls:
                file_name  = 'color_profile_%s.json' % (profile['camera_mode'])
                filepath = join(root_path, 'profiles', file_name)
                logger.info('writing profile to %s' % filepath)
                with open(filepath, mode='w') as f:
                    json.dump(profile, f, indent=4)


        logger.info('broadcasting to %s' % len(ControllerWS.watchers))
        for watcher in ControllerWS.watchers:
            watcher.write_message(message)

    def send_msg(self, msg):
        try:
            self.write_message(msg, False)
        except WebSocketClosedError:
            logger.warn("%s: websocket closed when sending message" % self.uid)

    ## this is used by NTSerial to send updates to web
    def send_msg_threadsafe(self, data):
        self.ioloop.add_callback(self.send_msg, data)

    def on_close(self):
        logger.info("Controller websocket closed %s" % self.uid)
        ControllerWS.watchers.remove(self)
