import serial
import time
from enum import Enum

class Symbol(Enum):
    CROSS = 1
    NOUGHT = 2

class Grbl:
    
    def __init__(self,
                 serial_port = "/dev/ttyUSB0",
                 grid_size = 20,
                 home = True):
        self.origin_x = 0
        self.origin_y = 0
        self.pen_up_position = 650
        self.pen_down_position = 965
        self.max_speed = 15000
        self.draw_speed = 3000
        self.grid_size = grid_size
        self.symbol = Symbol.CROSS
        print("Opening serial port")
        self.ser = serial.Serial(port = serial_port,
            baudrate = 115200,
            timeout = 1.0)
        print("Opened serial port")
        time.sleep(2)
        self.ser.flushInput()
        self.ser.write(b"$X\n")
        self.pen_up(True)
        if home:
            print("Homing")
            self.ser.write(b"$H\n")
        else:
            print("WARNING: Unlocked")
        time.sleep(0.5)
        self.wait_for_ok()

    def set_origin(self, x, y):
        self.origin_x = x
        self.origin_y = y
        
    def set_origin_t(self, xy):
        self.origin_x = xy[0]
        self.origin_y = xy[1]
        
    def set_symbol(self, sym):
        self.symbol = sym

    def wait_for_ok(self):
        while True:
            reply = self.ser.readline().strip()
            if reply == b'ok':
                #print("OK")
                break
            time.sleep(0.5)

    def goto(self, x, y, speed=10000):
        #print("Go to %d, %d" % (x, y))
        self.ser.write(b"G1X%dY%dF%d\n" % (-x, y, speed))
        self.wait_for_ok()
        while True:
            self.ser.write(b"?")
            reply = self.ser.readline().strip()
            if len(reply) > 0:
                parts = reply.split(b"|")
                if parts[0] == b'<Idle':
                    break
            time.sleep(0.1)

    def pen_up(self, up):
        #print("Pen %s" % ('up' if up else 'down'))
        pos = self.pen_up_position if up else self.pen_down_position
        self.ser.write(b"G4P0M3S%d\n" % pos)
        self.wait_for_ok()
        time.sleep(0.2)

    def draw_line(self, x1, y1, x2, y2, speed=None):
        move_speed = self.max_speed
        draw_speed = self.draw_speed
        if speed:
            move_speed = speed
            draw_speed = speed
        self.goto(x1, y1, speed=move_speed)
        self.pen_up(False)
        self.goto(x2, y2, speed=draw_speed)

    def draw_grid(self, speed=10000):
        self.draw_line(self.origin_x + 1*self.grid_size, self.origin_y,
                       self.origin_x + 1*self.grid_size, self.origin_y + 3*self.grid_size,
                       speed=speed)
        self.pen_up(True)
        self.draw_line(self.origin_x + 2*self.grid_size, self.origin_y + 3*self.grid_size,
                       self.origin_x + 2*self.grid_size, self.origin_y,
                       speed=speed)
        self.pen_up(True)
        self.draw_line(self.origin_x + 3*self.grid_size, self.origin_y + 1*self.grid_size,
                       self.origin_x, self.origin_y + 1*self.grid_size,
                       speed=speed)
        self.pen_up(True)
        self.draw_line(self.origin_x, self.origin_y + 2*self.grid_size,
                       self.origin_x + 3*self.grid_size, self.origin_y + 2*self.grid_size,
                       speed=speed)
        self.pen_up(True)
        self.goto(self.origin_x + 3*self.grid_size, self.origin_y + 3*self.grid_size, speed=self.max_speed)

    def draw_circle(self, x, y, radius, speed=None):
        # G0 X8.0000Y10.0000
        # G1 Z-0.0625F5.00
        # F5.00
        # G2 X8.0000Y10.0000 i2.0000j0 z-0.0625
        if not speed:
            speed = self.draw_speed
        self.ser.write(b"G0X%dY%d\n" % (-(x-radius), y))
        self.ser.write(b"G1F%d\n" % speed)
        self.ser.write(b"G2X%dY%dI%dJ0\n" % (-(x-radius), y, radius))
        self.wait_for_ok()
        while True:
            self.ser.write(b"?")
            reply = self.ser.readline().strip()
            if len(reply) > 0:
                parts = reply.split(b"|")
                if parts[0] == b'<Idle':
                    break
            time.sleep(0.1)
        
    def draw_symbol(self, x, y):
        self.pen_up(True)
        FILL = 0.7
        cx = self.origin_x + (x + 0.5) * self.grid_size
        cy = self.origin_y + (y + 0.5) * self.grid_size
        d = self.grid_size/2 * FILL
        if self.symbol == Symbol.CROSS:
            self.draw_line(cx - d, cy - d, cx + d, cy + d)
            self.pen_up(True)
            self.draw_line(cx - d, cy + d, cx + d, cy - d)
        else:
            self.draw_circle(cx, cy, d)
        self.pen_up(True)

if __name__ == "__main__":
    l = Grbl(home = True)
    if False:
        # Basic motion
        l.goto(10, 0)
        l.goto(0, 50, 3000)
        l.pen_up(False)
        l.goto(50, 50)
        l.pen_up(True)
        l.goto(0, 0)
    if True:
        # Grid
        xo = 100
        yo = 50
        l.set_origin(xo, yo)
        l.draw_grid(speed=15000)
        l.set_symbol(Symbol.CROSS)
        l.draw_symbol(1, 0)
        l.set_symbol(Symbol.NOUGHT)
        l.draw_symbol(0, 2)
        l.set_symbol(Symbol.CROSS)
        l.draw_symbol(-1, -1)
    if False:
        # Pen test
        for i in range(5):
            l.pen_up(False)
            time.sleep(3)
            l.pen_up(True)
            time.sleep(1)
