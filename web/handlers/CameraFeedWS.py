import uuid
from tornado.websocket import WebSocketHandler, WebSocketClosedError
import logging
import json
logger = logging.getLogger(__name__)

class CameraFeedWS(WebSocketHandler):
    """
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
                CameraFeedWS.watchers.add(self)
            if message == 'close feed':
                CameraFeedWS.watchers.remove(self)
        else:
            for waiter in CameraFeedWS.watchers:
                waiter.write_message(message, binary=True)

    def on_close(self):
        logger.info("CameraFeed websocket closed %s" % self.uid)
        if self in CameraFeedWS.watchers:
            CameraFeedWS.watchers.remove(self)
