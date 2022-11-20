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
from minimax import Game
from shapely.geometry import LineString, Point

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
# Pixel offset of GRBL zero
PIXEL_ZERO = (1265, 1005)
SQUARE_PIXELS = 300

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

def get_grid_pic(paper, active_square):
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
    return frame

def detect_grid_position(frame):
    h, v, xx, yy, output, nolines = detect.detect_grid(frame, 3*CAM_GRID_SIZE)
    print("Grid pos %d, %d   %d, %d" % (xx[0], yy[0], xx[1], yy[1]))
    cv2.imwrite('png/out.png', output)
    cv2.imwrite('png/nolines.png', nolines)
    return (xx, yy)
    
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
parser.add_argument('-p', '--skippaper',
                    help='Do not detect paper boundaries (reuse previous)',
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

if args.skippaper:
    progress('Loading paper position')
else:
    progress('Detecting paper')
    if not args.noplotter:
        plotter.goto(grbl.Grbl.MAX_X, grbl.Grbl.MAX_Y)
paper = detect_paper_boundaries(args.skippaper)
pen = compute_pen_boundaries()

while True:
    # start new game
    #cur_squares = [None for i in range(9)]
    board = Game() #(cur_squares)
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
        present(plotter, active_square_origin)

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
        if board.game_over():
            game_over = True
            display.show(1, '*** GAME OVER ***')
            print('Game over!')
            break

        my_symbol = board.get_enemy(human_symbol)
        print('Determining move for %c' % my_symbol)
        (m, computer_move_x, computer_move_y) = board.max_alpha_beta(-2, 2)
        progress('Playing %c at (%d, %d)' % (my_symbol, computer_move_x, computer_move_y))
        if plotter:
            plotter.set_symbol(grbl.Symbol.CROSS if my_symbol == 'X' else grbl.Symbol.NOUGHT)
            plotter.draw_symbol(computer_move_x, computer_move_y)
        board.make_move(computer_move_x, computer_move_y, my_symbol)

        if board.game_over():
            game_over = True
            display.show(1, '*** GAME OVER ***')
            print('Game over!')
            break

        # Make room for human
        present(plotter, active_square_origin)
