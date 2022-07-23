import serial
import time

class Grbl:
    
    def __init__(self, serial_port = "/dev/ttyUSB0"):
        print("Opening serial port")
        self.ser = serial.Serial(port = serial_port,
            baudrate = 115200,
            timeout = 1.0)
        print("Opened serial port")
        time.sleep(2)
        self.ser.flushInput()
        print("Homing")
        self.ser.write(b"$H\n")
        time.sleep(0.5)
        self.wait_for_ok()

    def wait_for_ok(self):
        while True:
            reply = self.ser.readline().strip()
            if reply == b'ok':
                print("OK")
                break
            time.sleep(0.5)

    def goto(self, x, y, speed=10000):
        print("Go to %d, %d" % (x, y))
        time.sleep(0.5)
        self.ser.write(b"G1X%dY%dF%d\n" % (-x, y, speed))
        self.wait_for_ok()
        while True:
            self.ser.write(b"?")
            reply = self.ser.readline().strip()
            if len(reply) > 0:
                parts = reply.split(b"|")
                if parts[0] == b'<Idle':
                    break
            time.sleep(0.2)

if __name__ == "__main__":
    l = Grbl()
    l.goto(10, 0)
    l.goto(0, 50, 3000)
    l.goto(50, 50)
    l.goto(0, 0)
    
