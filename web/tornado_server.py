import tornado.web
from tornado.ioloop import IOLoop
from os.path import abspath, dirname, join
import config
import logging
import controls

from web.handlers import NonCachingStaticFileHandler
from web.handlers import ControllerWS
from web.handlers import ObjectTrackingWS
from web.handlers import CameraFeedWS
from web.handlers import FarCameraFeedWS
from web.handlers import WideCameraFeedWS
from web.handlers import ProcessedVideoWS
from web.handlers import CalibrationFeedWS

from profiles.color_profile import ColorProfile
from controls import main_controller

logger = logging.getLogger(__name__)

def start():

    # setup tornado application with static handler + networktables support
    www_dir = abspath(join(dirname(__file__), "www"))
    #lib_dir = abspath(join(dirname(__file__), "www", "lib"))

    color_profile_map = {}
    for profile in [controls.CAMERA_MODE_RAW,
                    controls.CAMERA_MODE_BALL,
                    controls.CAMERA_MODE_HEXAGON,
                    controls.CAMERA_MODE_LOADING_BAY]:

        color_profile_map[profile] = ColorProfile(profile)

    app = tornado.web.Application(
        handlers=[
            ("/dashboard/ws", ControllerWS),
            ("/tracking/ws", ObjectTrackingWS),
            (r"/camera/ws", CameraFeedWS),
            (r"/wide_camera/ws", WideCameraFeedWS),
            (r"/far_camera/ws", FarCameraFeedWS),
            (r"/processed/ws", ProcessedVideoWS),
            (r"/calibration/ws", CalibrationFeedWS),
            (r"/calibrate/()", NonCachingStaticFileHandler, {"path": join(www_dir, "calibrate.html")}),
            (r"/processing/()", NonCachingStaticFileHandler, {"path": join(www_dir, "processed.html")}),
            (r"/camera/()", NonCachingStaticFileHandler, {"path": join(www_dir, "camera.html")}),
            (r"/wide_camera/()", NonCachingStaticFileHandler, {"path": join(www_dir, "camera.html")}),
            (r"/far_camera/()", NonCachingStaticFileHandler, {"path": join(www_dir, "camera.html")}),

            (r"/()", NonCachingStaticFileHandler, {"path": join(www_dir, "index.html")}),
            #(r'/lib/(.*)', StaticFileHandler, {"path": lib_dir}),
            (r"/(.*)", NonCachingStaticFileHandler, {"path": www_dir})
        ],
        sockets=[],
        color_profiles=color_profile_map
    )


    # Start the app
    logger.info("Listening on http://localhost:%s/", config.tornado_server_port)

    main_controller.color_profiles = color_profile_map

    app.listen(config.tornado_server_port)
    IOLoop.current().start()
