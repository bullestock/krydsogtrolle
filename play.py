import argparse
import cv2
import grbl
import numpy
from shapely.geometry import LineString, Point

port = 0
cam = cv2.VideoCapture(port)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1) # don't store old frames

grid_size = 15
square_size = 5*grid_size

def to_tuple(ls):
    return tuple([ls.coords[0], ls.coords[1]])

def to_list(t):
    return (int(t[0]), int(t[1]))

# Get cropped frame from camera
def get_frame():
    ret, frame = cam.read()
    assert ret == True, 'could not get picture for detecting paper boundaries'
    return frame[250:1600, 250:2000]
    
# Get paper boundaries in camera coordinates
def detect_paper_boundaries():
    frame = get_frame()
    cv2.imwrite('paper.png', frame)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    blur = cv2.medianBlur(gray, 5)
    ret, bin_img = cv2.threshold(blur, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    print("Threshold: %d" % ret)
    cv2.imwrite('binpaper.png', bin_img)
    contours, hierarchy = cv2.findContours(bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    im2 = frame
    cv2.drawContours(im2, contours, -1, (255, 0, 0), 2)
    cv2.imwrite('paperlines1.png', im2)
    paper_contours = []
    for c in contours:
        if len(c) > 3 and len(c) < 5:
            min_x = 9999
            max_x = 0
            for e in c:
                min_x = min(min_x, e[0][0])
                max_x = max(max_x, e[0][0])
            dx = max_x - min_x
            if dx > 100:
                print("c %s" % c)
                paper_contours.append(c)
            else:
                print("skip")
    im3 = frame
    cv2.drawContours(im3, paper_contours, -1, (0, 0, 255), 1)
    cv2.imwrite('paperimportantlines.png', im3)
    print(len(contours))
    print(len(paper_contours))
    return ((575, 310), (1930, 1245))

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
def find_next_free_square():
    return (0, 0)

# Proudly present our work
def present(plotter, active_square_origin):
    plotter.goto(active_square_origin[0] + grid_size + 2*square_size,
                 active_square_origin[1] + grid_size + 2*square_size)

# Enlarge an area by the specified amount on each side
def enlarge(area, amount):
    return ((max(0, area[0][0] - amount), max(0, area[0][1] - amount)),
            (max(0, area[1][0] + amount), max(0, area[1][1] + amount)))

def detect_grid_position(paper, pen, active_square_origin):
    get_frame() # flush old frame
    frame = get_frame()
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite("frame.png", frame)
    area_pen = (active_square_origin, (active_square_origin[0] + square_size,
                                       active_square_origin[1] + square_size))
    area_pen = enlarge(area_pen, grid_size/2)
    print("Pen: %s" % str(area_pen))
    area_cam = (convert_pen_to_paper(paper, pen, area_pen[0]),
                convert_pen_to_paper(paper, pen, area_pen[1]))
    print("Camera: %s" % str(area_cam))
    slice = frame[area_cam[1][0]:area_cam[1][1], area_cam[0][0]:area_cam[0][1]]
    slice = frame[1000:1400, 1300:1600]
    cv2.imwrite("slice.png", slice)

parser = argparse.ArgumentParser(description='Play noughts and crosses.')
parser.add_argument('-n', '--noplotter',
                    help='Do not connect to plotter', action='store_true')
args = parser.parse_args()

plotter = None
if not args.noplotter:
    plotter = grbl.Grbl(grid_size = grid_size)
    plotter.goto(grbl.Grbl.MAX_X, grbl.Grbl.MAX_Y)

paper = detect_paper_boundaries()
exit()
pen = compute_pen_boundaries()
active_square = find_next_free_square()
active_square_origin = (pen[0][0] + active_square[0] * square_size,
                        pen[0][1] + active_square[1] * square_size)
print("Active square: %s" % str(active_square_origin))

if plotter:
    # Set the origin
    plotter.set_origin_t(active_square_origin)
    # Set the scene
    plotter.draw_grid()
    # Make room for the human
    present(plotter, active_square_origin)

# Detect position of the grid
grid_pos = detect_grid_position(paper, pen, active_square_origin)
