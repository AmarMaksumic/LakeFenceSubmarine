NYUTRAL = 'NYUTRAL'
KOMPRESS = 'KOMPRESS'
EKSPEL = 'EKSPEL'

class Controls():

    def __init__(self):
        self.pump_mode = NYUTRAL
        self.servo_mode = NYUTRAL
        self.joy_x = 0
        self.joy_y = 0


    def update(message):
        print(message)

main_controller = Controls()
