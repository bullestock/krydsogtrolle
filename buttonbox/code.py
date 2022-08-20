import digitalio, board
import usb_hid
import time

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode

pin1 = digitalio.DigitalInOut(board.IO33)
pin1.pull = digitalio.Pull.DOWN
pin2 = digitalio.DigitalInOut(board.IO34)
pin2.pull = digitalio.Pull.DOWN
pin3 = digitalio.DigitalInOut(board.IO35)
pin3.pull = digitalio.Pull.DOWN

pin1last = False
pin2last = False
pin3last = False

kbd = Keyboard(usb_hid.devices)
n = 0
while True:
    time.sleep(0.5)
    n = n + 1
    if n > 5:
        pin1last = False
        pin2last = False
        pin3last = False
    if pin1.value and not pin1last:
        kbd.send(Keycode.F10)
        pin1last = True
    if pin2.value and not pin2last:
        kbd.send(Keycode.F11)
        pin2last = True
    if pin3.value and not pin3last:
        kbd.send(Keycode.F12)
        pin3last = True

