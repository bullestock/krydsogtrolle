import digitalio, board
import time

pin1 = digitalio.DigitalInOut(board.IO33)
pin1.pull = digitalio.Pull.DOWN
pin2 = digitalio.DigitalInOut(board.IO34)
pin2.pull = digitalio.Pull.DOWN
pin3 = digitalio.DigitalInOut(board.IO35)
pin3.pull = digitalio.Pull.DOWN

pin1last = False
pin2last = False
pin3last = False

time.sleep(3)

while True:
    time.sleep(0.01)
    if pin1.value:
        if not pin1last:
            print('A')
            pin1last = True
    else:
        pin1last = False
    if pin2.value:
        if not pin2last:
            print('B')
            pin2last = True
    else:
        pin2last = False
    if pin3.value:
        if not pin3last:
            print('C')
            pin3last = True
    else:
        pin3last = False
