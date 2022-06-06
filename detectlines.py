import cv2
import numpy
import math
from matplotlib import pyplot as plt
from shapely.geometry import LineString

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

def line_distance(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx*dx + dy*dy)

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
        if dx >= MIN_LEN and dy < MAX_DEV:
            # horizontal
            print("H")
            horizontal.append(((x1, y1), (x2, y2)))
        elif dy >= MIN_LEN and dx < MAX_DEV:
            # vertical
            print("V")
            vertical.append(((x1, y1), (x2, y2)))
        else:
            # neither
            print("skip")
            neither.append(((x1, y1), (x2, y2)))

horizontal_c = set()
vertical_c = set()
other = set()

# minimum extension beyond crossing point
MIN_EXTEND = 40

for h in horizontal:
    for v in vertical:
        c = line_intersection(h, v)
        is_crossing = False
        if c:
            print("hline: %d, %d -> %d, %d" % (h[0][0], h[0][1], h[1][0], h[1][1]))
            print("vline: %d, %d -> %d, %d" % (v[0][0], v[0][1], v[1][0], v[1][1]))
            print("cross: %d, %d" % (c[0], c[1]))
            dist1 = line_distance(h[0], c)
            dist2 = line_distance(h[1], c)
            dist3 = line_distance(v[0], c)
            dist4 = line_distance(v[1], c)
            if (dist1 >= MIN_EXTEND and dist2 >= MIN_EXTEND and
                dist3 >= MIN_EXTEND and dist4 >= MIN_EXTEND):
                is_crossing = True
            else:
                print("no: %d %d %d %d" % (dist1, dist2, dist3, dist4))
        if is_crossing:
            horizontal_c.add(h)
            vertical_c.add(v)
        else:
            other.add(h)
            other.add(v)

for h in horizontal_c:
    cv2.line(line_image, h[0], h[1], (0, 0, 255), 5)

for v in vertical_c:
    cv2.line(line_image, v[0], v[1], (0, 255, 0), 5)

#for v in other:
#    cv2.line(line_image, v[0], v[1], (255, 0, 0), 5)

#for h in neither:
#    cv2.line(line_image, h[0], h[1], (0, 255, 255), 5)

# Draw the lines on the  image
lines_edges = cv2.addWeighted(input, 0.8, line_image, 1, 0)
cv2.imwrite('out.png', lines_edges)



# TODO

# Calculate the intersections of each horizontal line with each vertical line

# TODO
