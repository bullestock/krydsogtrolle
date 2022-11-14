import argparse
import cv2
import grbl
import json
import numpy
import os
import subprocess
import detect
import display
from getkey import getkey, keys
from alphabeta import Tic, get_enemy, determine
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
# Pixel offset of GRBL zero
PIXEL_ZERO = (1265, 1005)
SQUARE_PIXELS = 300

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
    
# Return paper boundaries in camera coordinates
def detect_paper_boundaries(skip_paper_detection):
    frame = get_frame()
    cv2.imwrite('png/paper.png', frame)
    if skip_paper_detection:
        with open('paper.json', 'r') as f:
            saved = json.load(f)
            xmin = saved['xmin']
            xmax = saved['xmax']
            ymin = saved['ymin']
            ymax = saved['ymax']
            hd = saved['height']
            wd = saved['width']
    else:
        out = subprocess.run(["./a4detect", 'png/paper.png'], capture_output=True)
        assert out.returncode == 0, 'a4detect failed'
        strings = out.stdout.decode().splitlines()
        coords = []
        for s in strings:
            words = s.split(',')
            bounds = [int(x) for x in words]
            coords.append([bounds[0], bounds[1]])
            coords.append([bounds[2], bounds[3]])
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
        wd = int((xmax - xmin)/4)
        hd = int((ymax - ymin)/4)
        saved = { 'xmin': xmin, 'xmax': xmax,
                  'ymin': ymin, 'ymax': ymax,
                  'height': hd, 'width': wd }
        with open("paper.json", "w") as f:
            json.dump(saved, f)
    boundaries = ((xmin, ymin), (xmax, ymax))
    return boundaries

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
    cv2.imwrite("png/frame-paper.png", frame)
    # Cut out active square
    paper_width = paper[1][0] - paper[0][0]
    paper_height = paper[1][1] - paper[0][1]
    print("Paper boundary: %s w %d h %d" % (paper, paper_width, paper_height))
    aspect_ratio = paper_width/paper_height
    assert (aspect_ratio > 1.3) and (aspect_ratio < 1.5), 'wrong paper aspect ratio (%f)' % aspect_ratio
    square_w = SQUARE_PIXELS
    x2 = int(PIXEL_ZERO[0] - active_square[0]*square_w)
    x1 = int(x2 - square_w)
    EXTRA = 0#0.2
    if x2 < paper_width - square_w//2:
        x2 = int(x2 + EXTRA*square_w)
    if x1 > square_w//2:
        x1 = int(x1 - EXTRA*square_w)
    square_h = SQUARE_PIXELS
    y2 = int(PIXEL_ZERO[1] - active_square[1]*square_h)
    y1 = int(y2 - square_h)
    if y2 < paper_height - square_h//2:
        y2 = int(y2 + EXTRA*square_h)
    if y1 > square_h//2:
        y1 = int(y1 - EXTRA*square_h)
    print('Grid boundary: (%d, %d) (%d, %d)' % (x1, y1, x2, y2))
    frame = frame[y1:y2, x1:x2]
    cv2.imwrite("png/frame-square.png", frame)
    # Detect grid
    h, v, xx, yy, output, nolines = detect.detect_grid(frame, 4*GRID_SIZE)
    print("Grid pos %d, %d   %d, %d" % (xx[0], yy[0], xx[1], yy[1]))
    cv2.imwrite('png/out.png', output)
    cv2.imwrite('png/nolines.png', nolines)
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
    # cv2.imwrite("png/slice.png", slice)

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
    print('Please make your move')
    key = wait_key()
    print('%s was pressed' % key)
    print('OK!')

def wait_key():
    key = getkey()
    return key

# --- main ---

parser = argparse.ArgumentParser(description='Play noughts and crosses.')
parser.add_argument('-n', '--noplotter',
                    help='Do not connect to plotter', action='store_true')
parser.add_argument('-s', '--start',
                    help='Start square (default is (0, 0))')
parser.add_argument('-p', '--skippaper',
                    help='Do not detect paper boundaries (reuse previous)',
                    action='store_true')
args = parser.parse_args()

if not os.path.exists('png'):
    os.makedirs('png')

plotter = None
if not args.noplotter:
    plotter = grbl.Grbl(grid_size = GRID_SIZE)
    plotter.enable_logging()
    plotter.goto(grbl.Grbl.MAX_X, grbl.Grbl.MAX_Y)

board = Tic()

progress('Detecting paper')
paper = detect_paper_boundaries(args.skippaper)
pen = compute_pen_boundaries()

if args.start:
    start_args = args.start.split(',')
    if len(start_args) != 2:
        fatal_error('bad argument to --start: %s' % start_args)
    active_square_x = int(start_args[0])
    active_square_y = int(start_args[1])
    print('Starting at (%d, %d)' % (active_square_x, active_square_y))
    
while True:
    # start new game
    prev_symbols = BLANK_BOARD
    human_symbol = None
    game_over = False
    active_square = get_next_square()
    if not active_square[0]:
        fatal_error('out of paper')
    active_square_origin = (GRID_SIZE + pen[0][0] + active_square[0] * SQUARE_SIZE,
                            GRID_SIZE + pen[0][1] + active_square[1] * SQUARE_SIZE)
    print("Active square: %s" % str(active_square_origin))
    
    if plotter:
        # Set the origin
        plotter.set_origin_t(active_square_origin)
        # Set the scene
        progress('Drawing grid')
        plotter.draw_grid()
        # Make room for human
        present(plotter, active_square_origin)

    # start game loop
    while not game_over:

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
            cur_symbols = detect.detect_symbols(pic, xx, yy)
            if not cur_symbols:
                fatal_error('no symbols found')
            prefix = 'Board: '
            print("%s%s" % (prefix, print_board(cur_symbols, len(prefix))))

            if len(cur_symbols) != len(prev_symbols):
                fatal_error('board size changed')

            for i in range(0, len(cur_symbols)):
                if cur_symbols[i] != prev_symbols[i]:
                    print('New: %c at %d' % (cur_symbols[i], i))
                    if new_symbol:
                        fatal_error('more than one new symbol')
                    new_symbol = (i, cur_symbols[i])
            prev_symbols = cur_symbols

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
            progress('Playing %c at %d' % (my_symbol, computer_move))
            if plotter:
                plotter.set_symbol(grbl.Symbol.CROSS if my_symbol == 'X' else grbl.Symbol.NOUGHT)
                plotter.draw_symbol(index_to_x(computer_move), index_to_y(computer_move))
            print('make move')
            board.make_move(computer_move, my_symbol)

            print('check complete')
            if board.complete():
                game_over = True
                display.show(1, '*** GAME OVER ***')
                print('Game over!')
                break

            # Make room for human
            present(plotter, active_square_origin)
