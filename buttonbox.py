import serial

class ButtonBox:
    def __init__(self,
                 serial_port = "/dev/ttyACM0"):
        print("Opening button box serial port")
        self.ser = serial.Serial(port = serial_port,
            baudrate = 115200,
            timeout = 1.0)
        
    def wait_key(self):
        while True:
            reply = self.ser.readline().decode('ascii').strip()
            if len(reply) > 0:
                return reply

if __name__ == "__main__":
    bb = ButtonBox()
    while True:
        key = bb.wait_key()
        print('%s was pressed' % key)
