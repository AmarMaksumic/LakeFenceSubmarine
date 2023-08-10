import uuid
from tornado.websocket import WebSocketHandler, WebSocketClosedError
import logging
import json
logger = logging.getLogger(__name__)


class BaseCameraFeedWS(WebSocketHandler):
    """
    """
    def open(self):
        self.uid = str(uuid.uuid4()).split("-")[0]
        logger.info("%s websocket opened %s" % (self.__class__.__name__, self.uid))
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
        if isinstance(message, str):
            logger.info("%s %s %s" % (self.__class__.__name__, self.uid, message))
            if message == 'open feed':
                self.watchers.add(self)
            if message == 'close feed' :
                self.watchers.remove(self)
        else:
            for waiter in self.watchers:
                waiter.write_message(message, binary=True)

    def on_close(self):
        logger.info("%s websocket closed %s" % (self.__class__.__name__, self.uid))
        if self in self.watchers:
            self.watchers.remove(self)


class CameraFeedWS(BaseCameraFeedWS):
    watchers = set()

class FarCameraFeedWS(BaseCameraFeedWS):
    watchers = set()

class WideCameraFeedWS(BaseCameraFeedWS):
    watchers = set()
