import cv2
import grbl
from findcameras import list_ports

port = 0
cam = cv2.VideoCapture(port)
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1) # don't store old frames

grid_size = 15
square_size = 5*grid_size

# Get paper boundaries in camera coordinates
def detect_paper_boundaries():
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
    cam.read() # flush old frame
    ret, frame = cam.read()
    if not ret:
        print("Failed to grab frame from camera")
        quit()
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
    
plotter = grbl.Grbl(grid_size = grid_size)
paper = detect_paper_boundaries()
pen = compute_pen_boundaries()
active_square = find_next_free_square()
active_square_origin = (pen[0][0] + active_square[0] * square_size,
                        pen[0][1] + active_square[1] * square_size)
print("Active square: %s" % str(active_square_origin))

# Set the origin
plotter.set_origin_t(active_square_origin)
# Set the scene
plotter.draw_grid()
# Make room for the human
present(plotter, active_square_origin)
# Detect position of the grid
grid_pos = detect_grid_position(paper, pen, active_square_origin)
