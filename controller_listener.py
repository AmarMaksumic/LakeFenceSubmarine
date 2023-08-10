import logging
from controls import main_controller
import websocket
import json
import _thread as thread

logger = logging.getLogger(__name__)

def start(websocket_url):

    #websocket.enableTrace(True)
    def update_controls(ws, message):
        controls = json.loads(message)

        logger.info(controls)

        if 'pump' in controls:
            main_controller.pump_mode = controls['pump']

        if 'servo' in controls:
            main_controller.servo_mode = controls['servo']
        
        if 'joy_x' in controls:
            main_controller.joy_x = controls['joy_x']
        
        if 'joy_y' in controls:
            main_controller.joy_y = controls['joy_y']

        #logger.info(main_controller.color_profiles)

    def ws_closed(ws):
        logger.info('closed socket')

    def on_error(ws, error):
        print(error)

    def on_open(ws):
        main_controller.enable_camera = True


    def start_dashboard_socket(*args):

        dashboard_ws = websocket.WebSocketApp(websocket_url,
            on_message = update_controls,
            on_close=ws_closed,
            on_error = on_error)
        dashboard_ws.on_open = on_open
        dashboard_ws.run_forever()

    thread.start_new_thread(start_dashboard_socket, ())
