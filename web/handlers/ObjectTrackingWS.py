from os.path import abspath, dirname, join

import uuid
from tornado.websocket import WebSocketHandler, WebSocketClosedError
import logging

logger = logging.getLogger(__name__)

class ObjectTrackingWS(WebSocketHandler):
    """
    """
    watchers = set()
    def open(self):
        logger.info("ObjectTracking websocket opened")
        self.write_message('connected')
        ObjectTrackingWS.watchers.add(self)

    def check_origin(self, origin):
        """
            Allow CORS requests
        """
        return True

    """
    broadcast to clients, assumes its target data
    """
    def on_message(self, message):
        for waiter in ObjectTrackingWS.watchers:
            if waiter == self:
                continue
            waiter.write_message(message)

    def send_msg(self, msg):
        try:
            self.write_message(msg, False)
        except WebSocketClosedError:
            logger.warn("websocket closed when sending message")

    def on_close(self):
        logger.info("ObjectTracking websocket closed")
        ObjectTrackingWS.watchers.remove(self)
