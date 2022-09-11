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
        self.pen_up_position = 200
        self.pen_down_position = 700

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

    def pen(self, up):
        print("Pen %s" % ('up' if up else 'down'))
        pos = self.pen_up_position if up else self.pen_down_position
        self.ser.write(b"M3S%d\n" % pos)
        self.wait_for_ok()
        time.sleep(0.2)

    def line(self, x1, y1, x2, y2, speed=10000):
        self.goto(x1, y1, speed=speed)
        self.pen(False)
        self.goto(x2, y2, speed=speed)

    def grid(self, xo, yo, dist, speed=10000):
        l.line(xo + 1*dist, yo,
               xo + 1*dist, yo + 3*dist, speed=speed)
        l.pen(True)
        l.line(xo + 2*dist, yo + 3*dist,
               xo + 2*dist, yo, speed=speed)
        l.pen(True)
        l.line(xo, yo + 1*dist,
               xo + 3*dist, xo + 1*dist, speed=speed)
        l.pen(True)
        l.line(xo + 3*dist, xo + 2*dist,
               xo, yo + 2*dist, speed=speed)

if __name__ == "__main__":
    l = Grbl()
    if False:
        l.goto(10, 0)
        l.goto(0, 50, 3000)
        l.pen(False)
        l.goto(50, 50)
        l.pen(True)
        l.goto(0, 0)
    l.grid(80, 80, 40, speed=15000)
