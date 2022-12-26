# Standard modules
import argparse
import cv2
import grbl
import json
import numpy
import os
import subprocess
import time
from shapely.geometry import LineString, Point
# Local modules
import detect
import display
from getkey import getkey, keys
from minimax import Game

port = 0
cam = cv2.VideoCapture(port)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1) # don't store old frames

display = display.Display()
display.show(0, 'Starting')

GRBL_GRID_SIZE = 15
CAM_GRID_SIZE = 60
SQUARE_SIZE = 5*GRBL_GRID_SIZE
MAX_X_SQUARE = 4
MAX_Y_SQUARE = 3

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
def detect_paper_boundaries(do_paper_detection):
    frame = get_frame()
    cv2.imwrite('png/paper.png', frame)
    if not do_paper_detection:
        with open('paper.json', 'r') as f:
            saved = json.load(f)
            xmin = saved['xmin']
            xmax = saved['xmax']
            ymin = saved['ymin']
            ymax = saved['ymax']
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
        saved = { 'xmin': xmin, 'xmax': xmax,
                  'ymin': ymin, 'ymax': ymax }
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

# Enlarge an area by the specified amount on each side
def enlarge(area, amount):
    return ((max(0, area[0][0] - amount), max(0, area[0][1] - amount)),
            (max(0, area[1][0] + amount), max(0, area[1][1] + amount)))

def get_grid_pic(paper, active_square):
    get_frame() # flush old frame
    frame = get_paper_frame(paper)
    cv2.imwrite("png/frame-paper.png", frame)
    return frame

def detect_grid_position(frame):
    h, v, xx, yy, output, nolines = detect.detect_grid(frame, 3*CAM_GRID_SIZE)
    print("Grid pos %d, %d   %d, %d" % (xx[0], yy[0], xx[1], yy[1]))
    w = xx[1] - xx[0]
    h = yy[1] - yy[0]
    x1 = int(xx[0] - w/3)
    x2 = int(xx[1] + w/3)
    y1 = int(yy[0] - h/3)
    y2 = int(yy[1] + h/3)
    cv2.imwrite('png/out.png', output)
    cv2.imwrite('png/nolines.png', nolines)
    return ((x1, x2), (y1, y2))
    
def index_to_x(index):
    return index % 3

def index_to_y(index):
    return int(index / 3)

def fatal_error(msg):
    print('FATAL: %s' % msg)
    quit()

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
parser.add_argument('-p', '--detectpaper',
                    help='Detect paper boundaries (default: reuse previous)',
                    action='store_true')
args = parser.parse_args()

if args.start:
    start_args = args.start.split(',')
    if len(start_args) != 2:
        fatal_error('bad argument to --start: %s' % start_args)
    active_square_x = int(start_args[0])
    active_square_y = int(start_args[1])
    if (active_square_x < 0 or
        active_square_x > 3 or
        active_square_y < 0 or
        active_square_y > 2):
        fatal_error('bad coords in --start: %s' % start_args)
    print('Starting at (%d, %d)' % (active_square_x, active_square_y))
    
if not os.path.exists('png'):
    os.makedirs('png')

plotter = None
if not args.noplotter:
    plotter = grbl.Grbl(grid_size = GRBL_GRID_SIZE)
    plotter.enable_logging()

if args.detectpaper:
    progress('Detecting paper')
    if not args.noplotter:
        plotter.goto(grbl.Grbl.MAX_X, grbl.Grbl.MAX_Y)
        time.sleep(1)

paper = detect_paper_boundaries(args.detectpaper)
paper_width = paper[1][0] - paper[0][0]
paper_height = paper[1][1] - paper[0][1]
print("Paper boundary: %s w %d h %d" % (paper, paper_width, paper_height))
aspect_ratio = paper_width/paper_height
assert (aspect_ratio > 0.9) and (aspect_ratio < 1.1), 'wrong paper aspect ratio (%f)' % aspect_ratio

pen = compute_pen_boundaries()

while True:
    # start new game
    board = Game()
    human_symbol = None
    game_over = False
    active_square = get_next_square()
    if active_square[0] is None:
        fatal_error('out of paper')
    active_square_origin = (GRBL_GRID_SIZE + pen[0][0] + active_square[0] * SQUARE_SIZE,
                            GRBL_GRID_SIZE + pen[0][1] + active_square[1] * SQUARE_SIZE)
    print("Active square: %s" % str(active_square_origin))
    
    if plotter:
        # Set the origin
        plotter.set_origin_t(active_square_origin)
        # Set the scene
        progress('Drawing grid')
        plotter.draw_grid()
        # Make room for human
        plotter.present()

    # start game loop
    first = True
    while not game_over:

        # Wait for human move and detect new symbol
        cur_squares = board.get_board()
        new_symbol = None
        while not new_symbol:
            progress('Waiting for move')
            wait_for_human_move()

            # Detect position of the grid
            progress('Taking picture of grid')
            pic = get_grid_pic(paper, active_square)
            if first:
                progress('Detecting grid')
                xx, yy = detect_grid_position(pic)
                print("detect_grid_position: %s, %s" % (xx, yy))
            progress('Detecting symbols')
            pic = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
            new_squares = detect.detect_symbols(pic, xx, yy, cur_squares)
            if not new_squares:
                if not first:
                    fatal_error('no symbols found')
            else:
                print('Old:')
                board.show()
                print('New:')
                board.show(new_squares)

                if len(new_squares) != len(cur_squares):
                    fatal_error('board size changed')

                for y in range(0, len(new_squares)):
                    row = new_squares[y]
                    for x in range(0, len(row)):
                        if row[x] != cur_squares[y][x]:
                            if row[x] == '.':
                                fatal_error('New symbol at (%d, %d) is None' % (x, y))
                            print('New: %c at (%d, %d)' % (row[x], x, y))
                            if new_symbol:
                                fatal_error('more than one new symbol')
                            new_symbol_x = x
                            new_symbol_y = y
                            new_symbol = row[x]

        first = False

        display.show(1, '%c at %d, %d' % (new_symbol, new_symbol_x, new_symbol_y))
        if human_symbol is None:
            human_symbol = new_symbol
            board.set_human(human_symbol)
            print('Human is playing %c' % human_symbol)
        elif new_symbol != human_symbol:
            fatal_error('Illegal human move: %c' % new_symbol[1])

        board.make_move(new_symbol_x, new_symbol_y, new_symbol)
        go = board.game_over()
        if go:
            game_over = True
            display.show(1, '*** GAME OVER ***')
            print('Game over!')
            if plotter and go[0] != '.':
                plotter.show_winner(go[1], go[2])
            break

        my_symbol = board.get_enemy(human_symbol)
        print('Determining move for %c' % my_symbol)
        (m, computer_move_x, computer_move_y) = board.get_computer_move()
        progress('Playing %c at (%d, %d)' % (my_symbol, computer_move_x, computer_move_y))
        if plotter:
            plotter.set_symbol(grbl.Symbol.CROSS if my_symbol == 'X' else grbl.Symbol.NOUGHT)
            plotter.draw_symbol(computer_move_x, computer_move_y)
        board.make_computer_move(computer_move_x, computer_move_y)

        if board.game_over():
            game_over = True
            display.show(1, '*** GAME OVER ***')
            print('Game over!')
            break

        # Make room for human
        plotter.present()
