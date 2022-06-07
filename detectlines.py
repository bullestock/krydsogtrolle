import cv2
import numpy
import math
from matplotlib import pyplot as plt
from shapely.geometry import LineString, Point

def to_tuple(ls):
    return tuple([ls.coords[0], ls.coords[1]])

def to_list(t):
    return (int(t[0]), int(t[1]))
    
if False:
    # capture from camera
    cam = cv2.VideoCapture(2)

    ret, input = cam.read()
    if not ret:
        print("failed to grab frame")
        exit()
    cv2.imwrite('in.png', input)
else:
    # use precaptured image
    input = cv2.imread('in.png')

gray = cv2.cvtColor(input, cv2.COLOR_BGR2GRAY)

cv2.imwrite('gray.png', gray)

blur = cv2.medianBlur(gray, 5)
adapt_type = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
thresh_type = cv2.THRESH_BINARY_INV
bin_img = cv2.adaptiveThreshold(blur, 255, adapt_type, thresh_type, 11, 2)
cv2.imwrite('bin.png', bin_img)

rho = 1  # distance resolution in pixels of the Hough grid
theta = numpy.pi / 180  # angular resolution in radians of the Hough grid
threshold = 15  # minimum number of votes (intersections in Hough grid cell)
min_line_length = 50  # minimum number of pixels making up a line
max_line_gap = 20  # maximum gap in pixels between connectable line segments

# Run Hough on edge detected image
# Output "lines" is an array containing endpoints of detected line segments
lines = cv2.HoughLinesP(bin_img, rho, theta, threshold, numpy.array([]),
                        min_line_length, max_line_gap)

# Segment lines into horizontal and vertical

line_image = numpy.copy(input) * 0  # creating a blank to draw lines on

MIN_LEN = 200
MAX_DEV = 70 # max deviation from horizontal/vertical
horizontal = []
vertical = []
neither = []

for line in lines:
    for x1, y1, x2, y2 in line:
        dx = abs(x1 - x2)
        dy = abs(y1 - y2)
        print("line: %d, %d, %d, %d" % (x1, y1, x2, y2))
        p1 = Point(x1, y1)
        p2 = Point(x2, y2)
        ls = LineString([p1, p2])
        if dx >= MIN_LEN and dy < MAX_DEV:
            # horizontal
            print("H")
            horizontal.append(ls)
        elif dy >= MIN_LEN and dx < MAX_DEV:
            # vertical
            print("V")
            vertical.append(ls)
        else:
            # neither
            print("skip")
            neither.append(ls)

horizontal_c = set()
vertical_c = set()
other = set()

# minimum extension beyond crossing point
MIN_EXTEND = 40

for h in horizontal:
    for v in vertical:
        c = h.intersection(v)
        is_crossing = False
        if c:
            print("hline: %s -> %s" % (h.coords[0], h.coords[1]))
            print("vline: %s -> %s" % (v.coords[0], v.coords[1]))
            print("cross: %s" % c)
            dist1 = Point(h.coords[0]).distance(c)
            dist2 = Point(h.coords[1]).distance(c)
            dist3 = Point(v.coords[0]).distance(c)
            dist4 = Point(v.coords[1]).distance(c)
            if (dist1 >= MIN_EXTEND and dist2 >= MIN_EXTEND and
                dist3 >= MIN_EXTEND and dist4 >= MIN_EXTEND):
                is_crossing = True
            else:
                print("no: %d %d %d %d" % (dist1, dist2, dist3, dist4))
        if is_crossing:
            horizontal_c.add(to_tuple(h))
            vertical_c.add(to_tuple(v))
        else:
            other.add(to_tuple(h))
            other.add(to_tuple(v))

# for v in other:
#     cv2.line(line_image, to_list(v[0]), to_list(v[1]), (255, 0, 0), 5)

# for v in neither:
#     cv2.line(line_image, (int(v.coords[0][0]), int(v.coords[0][1])),
#              (int(v.coords[1][0]), int(v.coords[1][1])), (0, 255, 255), 5)

for h in horizontal_c:
    cv2.line(line_image, to_list(h[0]), to_list(h[1]), (0, 0, 255), 5)

for v in vertical_c:
    cv2.line(line_image, to_list(v[0]), to_list(v[1]), (0, 255, 0), 5)

    
# Draw the lines on the  image
lines_edges = cv2.addWeighted(input, 0.8, line_image, 1, 0)
cv2.imwrite('out.png', lines_edges)
