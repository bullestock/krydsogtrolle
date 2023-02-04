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
while True:
    time.sleep(0.01)
    if pin1.value:
        if not pin1last:
            kbd.press(Keycode.A)
            kbd.release_all()
            pin1last = True
    else:
        pin1last = False
    if pin2.value:
        if not pin2last:
            kbd.press(Keycode.B)
            kbd.release_all()
            pin2last = True
    else:
        pin2last = False
    if pin3.value:
        if not pin3last:
            kbd.press(Keycode.C)
            kbd.release_all()
            pin3last = True
    else:
        pin3last = False
