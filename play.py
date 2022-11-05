import argparse
import cv2
import grbl
import numpy
import subprocess
import detect
import display
from alphabeta import Tic, get_enemy, determine
from pynput import keyboard
from shapely.geometry import LineString, Point

port = 0
cam = cv2.VideoCapture(port)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1) # don't store old frames

display = display.Display()
display.show(0, 'Starting')

GRID_SIZE = 15
SQUARE_SIZE = 5*GRID_SIZE
MAX_X_SQUARE = 4
MAX_Y_SQUARE = 3

BLANK_BOARD = '         '

active_square_x = 0
active_square_y = 0

def progress(msg):
    global display
    display.show(0, msg)
    print(msg)
    
def to_tuple(ls):
    return tuple([ls.coords[0], ls.coords[1]])

def to_list(t):
    return (int(t[0]), int(t[1]))

# Get cropped frame from camera
def get_frame():
    ret, frame = cam.read()
    assert ret == True, 'could not get picture from camera'
    # Crop uninteresting parts
    frame = frame[250:1600, 250:2000]
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    return frame
    
def get_paper_frame(paper):
    frame = get_frame()
    frame = frame[paper[0][1]:paper[1][1], paper[0][0]:paper[1][0]]
    return frame
    
# Return a tuple of (paper boundaries in camera coordinates, average intensity of paper area)
def detect_paper_boundaries():
    frame = get_frame()
    cv2.imwrite('paper.png', frame)
    out = subprocess.run(["./a4detect", 'paper.png'], capture_output=True)
    assert out.returncode == 0, 'a4detect failed'
    strings = out.stdout.decode().splitlines()
    #print(strings)
    coords = []
    for s in strings:
        words = s.split(',')
        bounds = [int(x) for x in words]
        coords.append([bounds[0], bounds[1]])
        coords.append([bounds[2], bounds[3]])
    #print(coords)
    xsum = 0
    ysum = 0
    for c in coords:
        xsum = xsum + c[0]
        ysum = ysum + c[1]
    xavg = xsum/len(coords)
    yavg = ysum/len(coords)
    xmin = 99999
    xmax = 0
    ymin = 99999
    ymax = 0
    for c in coords:
        if c[0] > xavg:
            xmax = max(xmax, c[0])
        else:
            xmin = min(xmin, c[0])
        if c[1] > yavg:
            ymax = max(ymax, c[1])
        else:
            ymin = min(ymin, c[1])
    boundaries = ((xmin, ymin), (xmax, ymax))
    wd = int((xmax - xmin)/4)
    hd = int((ymax - ymin)/4)
    paper_frame = cv2.cvtColor(frame[ymin+hd:ymax-hd, xmin+wd:xmax-wd], cv2.COLOR_BGR2GRAY)
    #cv2.imwrite('paper_frame.png', paper_frame)
    avg = cv2.mean(paper_frame) # (avg, 0, 0, 0)
    return (boundaries, int(avg[0]))

# Compute pen boundaries in GRBL coordinates
def compute_pen_boundaries():
    return ((0, 0), (200, 250))

# Given camera and pen boundaries, convert pen coords to camera coords
def convert_pen_to_paper(cb, pb, xy):
    return (max(0, int((cb[1][0] - xy[0])*(pb[1][0]/(cb[1][0] - pb[0][0])))),
            max(0, int((xy[1] - cb[0][1])*pb[1][1]/(cb[1][1] - cb[0][1]))))

def convert_paper_to_pen(cb, pb, xy):
    return (max(0, int(cb[1][0] - (xy[0]*(cb[1][0] - cb[0][0])/pb[1][0]))),
            max(0, int(cb[0][1] + xy[1]/pb[1][1]/(cb[1][1] - cb[0][1]))))

# Find next free square
def get_next_square():
    global active_square_x, active_square_y
    sq = (active_square_x, active_square_y)
    active_square_x = active_square_x + 1
    if active_square_x >= MAX_X_SQUARE:
        active_square_x = 0
        active_square_y = active_square_y + 1
        if active_square_y >= MAX_Y_SQUARE:
            active_square_x = None
            active_square_y = None
    return sq

# Proudly present our work
def present(plotter, active_square_origin):
    # TODO
    plotter.goto(grbl.Grbl.MAX_X, grbl.Grbl.MAX_Y)

# Enlarge an area by the specified amount on each side
def enlarge(area, amount):
    return ((max(0, area[0][0] - amount), max(0, area[0][1] - amount)),
            (max(0, area[1][0] + amount), max(0, area[1][1] + amount)))

def detect_grid_position(paper, pen, active_square):
    get_frame() # flush old frame
    frame = get_paper_frame(paper)
    cv2.imwrite("frame-paper.png", frame)
    # Cut out active square
    paper_width = paper[1][0] - paper[0][0]
    paper_height = paper[1][1] - paper[0][1]
    print("Paper boundary: %s w %d h %d" % (paper, paper_width, paper_height))
    assert (paper_width/paper_height > 1.3) and (paper_width/paper_height < 1.5), 'wrong paper aspect ratio'
    square_w = int(paper_width/MAX_X_SQUARE)
    x2 = int((MAX_X_SQUARE - active_square[0])*square_w)
    x1 = int(x2 - square_w)
    if x2 < paper_width - square_w//2:
        x2 = x2 + square_w//2
    if x1 > square_w//2:
        x1 = x1 - square_w//2
    square_h = int(paper_height/MAX_Y_SQUARE)
    y2 = int((MAX_Y_SQUARE - active_square[1])*square_h)
    y1 = int(y2 - square_h)
    if y2 < paper_height - square_h//2:
        y2 = y2 + square_h//2
    if y1 > square_h//2:
        y1 = y1 - square_h//2
    print(x1, x2, y1, y2)
    frame = frame[y1:y2, x1:x2]
    cv2.imwrite("frame-square.png", frame)
    # Detect grid
    h, v, xx, yy, output, nolines = detect.detect_grid(frame, 4*GRID_SIZE)
    print("Grid pos %d, %d   %d, %d" % (xx[0], yy[0], xx[1], yy[1]))
    cv2.imwrite('out.png', output)
    cv2.imwrite('nolines.png', nolines)
    return (frame, xx, yy)
    
    # area_pen = (active_square_origin, (active_square_origin[0] + SQUARE_SIZE,
    #                                    active_square_origin[1] + SQUARE_SIZE))
    # area_pen = enlarge(area_pen, GRID_SIZE/2)
    # print("Pen: %s" % str(area_pen))
    # area_cam = (convert_pen_to_paper(paper, pen, area_pen[0]),
    #             convert_pen_to_paper(paper, pen, area_pen[1]))
    # print("Camera: %s" % str(area_cam))
    # slice = frame[area_cam[1][0]:area_cam[1][1], area_cam[0][0]:area_cam[0][1]]
    # slice = frame[1000:1400, 1300:1600]
    # cv2.imwrite("slice.png", slice)

def index_to_x(index):
    return index % 3

def index_to_y(index):
    return int(index / 3)

def fatal_error(msg):
    print('FATAL: %s' % msg)
    quit()

def print_board(s, pad):
    pre = pad * ' '
    return "%s\n%s%s\n%s%s" % (s[0:3], pre, s[3:6], pre, s[6:9])

def wait_for_human_move():
    input('Please make your move')
    print('OK!')

def wait_key():
    ''' Wait for a key press on the console and return it. '''
    result = None
    def on_press(key):
        nonlocal result
        result = key

    def on_release(key):
        # Stop listener
        return False

    # Collect events until released
    with keyboard.Listener(
            on_press=on_press,
            on_release=on_release) as listener:
        listener.join()    
    return result

# --- main ---

parser = argparse.ArgumentParser(description='Play noughts and crosses.')
parser.add_argument('-n', '--noplotter',
                    help='Do not connect to plotter', action='store_true')
args = parser.parse_args()

plotter = None
if not args.noplotter:
    plotter = grbl.Grbl(grid_size = GRID_SIZE)
    plotter.goto(grbl.Grbl.MAX_X, grbl.Grbl.MAX_Y)

board = Tic()

progress('Detecting paper')
paper, avg = detect_paper_boundaries()
print(avg)
print('Average paper pixel value %s' % avg)
pen = compute_pen_boundaries()
active_square = get_next_square()
active_square_origin = (pen[0][0] + active_square[0] * SQUARE_SIZE,
                        pen[0][1] + active_square[1] * SQUARE_SIZE)
print("Active square: %s" % str(active_square_origin))

# start main game loop
prev_symbols = BLANK_BOARD
human_symbol = None
game_over = False

while not game_over:
    
    if plotter:
        # Set the origin
        plotter.set_origin_t(active_square_origin)
        # Set the scene
        progress('Drawing grid')
        plotter.draw_grid()
        # Make room for the human
        present(plotter, active_square_origin)

    # Wait for human move and detect new symbol
    new_symbol = None
    while not new_symbol:
        progress('Waiting for move')
        wait_for_human_move()

        # Detect position of the grid
        progress('Detecting symbols')
        pic, xx, yy = detect_grid_position(paper, pen, active_square)
        pic = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
        print("detect_grid_position: %s, %s" % (xx, yy))
        cur_symbols = detect.detect_symbols(pic, xx, yy, avg)
        prefix = 'Board: '
        print("%s%s" % (prefix, print_board(cur_symbols, len(prefix))))

        if len(cur_symbols) != len(prev_symbols):
            fatal_error('board size changed')

        for i in range(0, len(cur_symbols)):
            if cur_symbols[i] != prev_symbols[i]:
                if new_symbol:
                    fatal_error('more than one new symbol')
                new_symbol = (i, cur_symbols[i])

    new_symbol_x = index_to_x(new_symbol[0])
    new_symbol_y = index_to_y(new_symbol[0])
    print('New symbol: %c at %d, %d' % (new_symbol[1], new_symbol_x, new_symbol_y))
    display.show(1, '%c at %d, %d' % (new_symbol[1], new_symbol_x, new_symbol_y))
    if human_symbol is None:
        human_symbol = new_symbol[1]
        print('Human is playing %c' % human_symbol)
    elif new_symbol[1] != human_symbol:
        fatal_error('Illegal human move: %c' % new_symbol[1])

    board.make_move(new_symbol[0], new_symbol[1])
    if board.complete():
        game_over = True
        display.show(1, '*** GAME OVER ***')
        print('Game over!')
        break

    my_symbol = get_enemy(human_symbol)
    print('Determining move for %c' % my_symbol)
    computer_move = determine(board, my_symbol)
    print('Placing %c at %d' % (my_symbol, computer_move))
    if plotter:
        print('set')
        plotter.set_symbol(my_symbol)
        print('draw')
        plotter.draw_symbol(index_to_x(computer_move), index_to_y(computer_move))
    print('make move')
    board.make_move(computer_move, my_symbol)

    print('check complete')
    if board.complete():
        game_over = True
        display.show(1, '*** GAME OVER ***')
        print('Game over!')
        break
    
