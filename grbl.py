import argparse
import serial
import time
from enum import Enum

class Symbol(Enum):
    CROSS = 1
    NOUGHT = 2

class Grbl:
    MAX_X = 345
    MAX_Y = 260
    def __init__(self,
                 serial_port = "/dev/ttyUSB0",
                 grid_size = 20,
                 home = True):
        self.logfile = None
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
        self.write(b"$X\n")
        self.pen_up(True)
        if home:
            print("Homing")
            self.write(b"$H\n")
        else:
            print("WARNING: Unlocked")
        time.sleep(0.5)
        self.wait_for_ok()

    def enable_logging(self):
        self.logfile = open("grbl.log", "w")

    def write(self, s):
        if self.logfile:
            self.logfile.write(s.decode('ascii'))
        self.ser.write(s)
        
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
        self.write(b"G1X%dY%dF%d\n" % (-x, y, speed))
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
        self.write(b"G4P0M3S%d\n" % pos)
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
        self.write(b"G0X%dY%d\n" % (-(x-radius), y))
        self.pen_up(False)
        self.write(b"G1F%d\n" % speed)
        self.write(b"G2X%dY%dI%dJ0\n" % (-(x-radius), y, radius))
        self.wait_for_ok()
        while True:
            self.write(b"?")
            reply = self.ser.readline().strip()
            if len(reply) > 0:
                parts = reply.split(b"|")
                if parts[0] == b'<Idle':
                    break
            time.sleep(0.1)
        self.pen_up(True)

    def draw_symbol(self, x, y):
        """
        Draw current symbol at (x, y)
          X  0  1  2
        Y
        0    .  .  .
        1    .  .  .
        2    .  .  .
        """
        self.pen_up(True)
        FILL = 0.65
        cx = self.origin_x + (2 - x + 0.5) * self.grid_size # X axis is positive left -> right
        cy = self.origin_y + (2 - y + 0.5) * self.grid_size # Y axis is positive bottom -> top
        d = self.grid_size/2 * FILL
        if self.symbol == Symbol.CROSS:
            self.draw_line(cx - d, cy - d, cx + d, cy + d)
            self.pen_up(True)
            self.draw_line(cx - d, cy + d, cx + d, cy - d)
        else:
            self.draw_circle(cx, cy, d)
        self.pen_up(True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control plotter.')
    parser.add_argument('--goto-max',
                        help='Go to maximum X/Y', action='store_true')
    parser.add_argument('--dot',
                        help='Make a dot at the specified position')
    args = parser.parse_args()
    l = Grbl(home = True)
    if args.goto_max:
        l.goto(Grbl.MAX_X, Grbl.MAX_Y)
        exit()
    if args.dot:
        dot_args = args.dot.split(',')
        if len(dot_args) != 2:
            fatal_error('bad argument to --dot: %s' % dot_args)
        l.goto(int(dot_args[0]), int(dot_args[1]))
        l.pen_up(False)
        l.pen_up(True)
        exit()
    if False:
        # Basic motion
        l.goto(10, 0)
        l.goto(0, 50, 3000)
        l.pen_up(False)
        l.goto(50, 50)
        l.pen_up(True)
        l.goto(0, 0)
    if False:
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
