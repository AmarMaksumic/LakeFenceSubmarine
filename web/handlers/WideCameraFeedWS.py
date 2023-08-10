import uuid
from tornado.websocket import WebSocketHandler, WebSocketClosedError
import logging
import json
logger = logging.getLogger(__name__)

class WideCameraFeedWS(WebSocketHandler):
    """
    """
    watchers = set()
    def open(self):
        self.uid = str(uuid.uuid4())
        logger.info("WideCameraFeed websocket opened %s" % self.uid)
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
                WideCameraFeedWS.watchers.add(self)
            if message == 'close feed':
                WideCameraFeedWS.watchers.remove(self)
        else:
            for waiter in WideCameraFeedWS.watchers:
                waiter.write_message(message, binary=True)

    def on_close(self):
        logger.info("CameraFeed websocket closed %s" % self.uid)
        if self in WideCameraFeedWS.watchers:
            WideCameraFeedWS.watchers.remove(self)
