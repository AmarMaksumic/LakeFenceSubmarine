import uuid
from tornado.websocket import WebSocketHandler, WebSocketClosedError
import logging
import json
logger = logging.getLogger(__name__)

class FarCameraFeedWS(WebSocketHandler):
    """
    watchers is a class level array, anyone connecting shares the same array
    """
    watchers = set()
    def open(self):
        self.uid = str(uuid.uuid4())
        logger.info("CameraFeed websocket opened %s" % self.uid)
        self.write_message('connected')
        self.write_message(json.dumps({
            'socketid':self.uid
        }))

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
        if isinstance(message, str):
            logger.info(message)
            if message == 'open feed':
                FarCameraFeedWS.watchers.add(self)
            if message == 'close feed':
                FarCameraFeedWS.watchers.remove(self)
        else:
            for waiter in FarCameraFeedWS.watchers:
                waiter.write_message(message, binary=True)

    def on_close(self):
        logger.info("CameraFeed websocket closed %s" % self.uid)
        if self in FarCameraFeedWS.watchers:
            FarCameraFeedWS.watchers.remove(self)
