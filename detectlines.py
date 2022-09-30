import cv2
import numpy
import math
from matplotlib import pyplot as plt
from shapely.geometry import LineString, Point

DEBUG = True

def to_tuple(ls):
    return tuple([ls.coords[0], ls.coords[1]])

def to_list(t):
    return (int(t[0]), int(t[1]))

# Find grid in an image
def detect_grid(input, min_length):
    gray = cv2.cvtColor(input, cv2.COLOR_BGR2GRAY)

    if DEBUG:
        cv2.imwrite('gray.png', gray)

    blur = cv2.medianBlur(gray, 5)
    adapt_type = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    thresh_type = cv2.THRESH_BINARY_INV
    bin_img = cv2.adaptiveThreshold(blur, 255, adapt_type, thresh_type, 11, 2)
    if DEBUG:
        cv2.imwrite('bin.png', bin_img)

    rho = 1  # distance resolution in pixels of the Hough grid
    theta = numpy.pi / 180  # angular resolution in radians of the Hough grid
    threshold = 15  # minimum number of votes (intersections in Hough grid cell)
    min_line_length = min_length/3  # minimum number of pixels making up a line
    max_line_gap = 20  # maximum gap in pixels between connectable line segments

    # Run Hough on edge detected image
    # Output "lines" is an array containing endpoints of detected line segments
    lines = cv2.HoughLinesP(bin_img, rho, theta, threshold, numpy.array([]),
                            min_line_length, max_line_gap)

    # Segment lines into horizontal and vertical

    line_image = numpy.copy(input) * 0  # creating a blank to draw lines on

    MAX_DEV = 70 # max deviation from horizontal/vertical
    horizontal = []
    vertical = []
    neither = []

    for line in lines:
        for x1, y1, x2, y2 in line:
            dx = abs(x1 - x2)
            dy = abs(y1 - y2)
            if DEBUG:
                print("line: %d, %d, %d, %d" % (x1, y1, x2, y2))
            p1 = Point(x1, y1)
            p2 = Point(x2, y2)
            ls = LineString([p1, p2])
            if dx >= min_length and dy < MAX_DEV:
                # horizontal
                if DEBUG:
                    print("H")
                horizontal.append(ls)
            elif dy >= min_length and dx < MAX_DEV:
                # vertical
                if DEBUG:
                    print("V")
                vertical.append(ls)
            else:
                # neither
                if DEBUG:
                    print("skip")
                neither.append(ls)

    horizontal_c = set()
    vertical_c = set()
    other = set()

    # minimum extension beyond crossing point
    MIN_EXTEND = 40

    # Find line that cross and are sufficiently long
    for h in horizontal:
        for v in vertical:
            c = h.intersection(v)
            is_crossing = False
            if c:
                if DEBUG:
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
                    if DEBUG:
                        print("no: %d %d %d %d" % (dist1, dist2, dist3, dist4))
            if is_crossing:
                horizontal_c.add(to_tuple(h)) # LineString is not hashable
                vertical_c.add(to_tuple(v))
            else:
                other.add(to_tuple(h))
                other.add(to_tuple(v))

    # Draw H and V lines
    for h in horizontal_c:
        cv2.line(line_image, to_list(h[0]), to_list(h[1]), (0, 255, 255), 3)

    for v in vertical_c:
        cv2.line(line_image, to_list(v[0]), to_list(v[1]), (0, 255, 0), 3)

    # Find boundaries of grid
    print("H: %s" % horizontal_c)
    print("V: %s" % vertical_c)
    count = 0
    x1avg = 0
    x2avg = 0
    for ls in horizontal_c:
        x1 = ls[0][0]
        x2 = ls[1][0]
        if x1 > x2:
            x1, x2 = x2, x1
        print("H X %d %d" % (x1, x2))
        x1avg = x1avg + x1
        x2avg = x2avg + x2
        count = count + 1
    x1avg = int(x1avg/count)
    x2avg = int(x2avg/count)
    count = 0
    y1avg = 0
    y2avg = 0
    for ls in vertical_c:
        y1 = ls[0][1]
        y2 = ls[1][1]
        if y1 > y2:
            y1, y2 = y2, y1
        y1avg = y1avg + y1
        y2avg = y2avg + y2
        #print("%d %d" % (y1, y2))
        count = count + 1
    y1avg = int(y1avg/count)
    y2avg = int(y2avg/count)
    print("X %d - %d" % (x1avg, x2avg))
    print("Y %d - %d" % (y1avg, y2avg))

    cv2.rectangle(line_image, (x1avg, y1avg), (x2avg, y2avg), (0, 0, 255), 1)

    # Add lines to the original image
    lines_edges = cv2.addWeighted(input, 0.8, line_image, 1, 0)

    return (horizontal_c, vertical_c, (x1avg, x2avg), (y1avg, y2avg), lines_edges)

if __name__ == "__main__":
    input = cv2.imread('slice.png')
    h, v, xx, yy, output = detect_grid(input, 150)
    cv2.imwrite('out.png', output)
    
