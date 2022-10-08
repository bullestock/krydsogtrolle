import cv2
import numpy
import math
from shapely.geometry import LineString, Point

DEBUG = True
SILLYDEBUG = False

def to_tuple(ls):
    return tuple([ls.coords[0], ls.coords[1]])

def to_list(t):
    return (int(t[0]), int(t[1]))

# Quantize an image
def quantize(img, nof_colors):
    Z = img.reshape((-1, 3))
    # convert to np.float32
    Z = numpy.float32(Z)
    # define criteria, number of clusters(K) and apply kmeans()
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label, center = cv2.kmeans(Z, nof_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    # Now convert back into uint8, and make original image
    center = numpy.uint8(center)
    res = center[label.flatten()]
    quantized = res.reshape((img.shape))
    return quantized

# Find grid in an image
def detect_grid(input, min_length):
    gray = cv2.cvtColor(input, cv2.COLOR_BGR2GRAY)

    if DEBUG:
        cv2.imwrite('gray.png', gray)

    blur = cv2.medianBlur(gray, 5)
    if DEBUG:
        cv2.imwrite('blur.png', blur)
    adapt_type = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    thresh_type = cv2.THRESH_BINARY_INV
    #bin_img = cv2.adaptiveThreshold(gray, 255, adapt_type, thresh_type, 11, 2)
    ret, bin_img = cv2.threshold(gray, 128, 255, thresh_type + cv2.THRESH_OTSU)
    print("Threshold: %d" % ret)
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
            if SILLYDEBUG:
                print("line: %d, %d, %d, %d" % (x1, y1, x2, y2))
            p1 = Point(x1, y1)
            p2 = Point(x2, y2)
            ls = LineString([p1, p2])
            if dx >= min_length and dy < MAX_DEV:
                # horizontal
                if SILLYDEBUG:
                    print("H")
                horizontal.append(ls)
            elif dy >= min_length and dx < MAX_DEV:
                # vertical
                if SILLYDEBUG:
                    print("V")
                vertical.append(ls)
            else:
                # neither
                if SILLYDEBUG:
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
                if SILLYDEBUG:
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
                    if SILLYDEBUG:
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
    if SILLYDEBUG:
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
        if SILLYDEBUG:
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

    # Remove lines:
    # 1) Find unique colours
    colors, count = numpy.unique(input.reshape(-1, input.shape[-1]), axis=0, return_counts=True)
    # 2) Use most common colour as background
    background = colors[count.argmax()]
    background = (int(background[0]), int(background[1]), int(background[2]))

    nolines = input
    for h in horizontal_c:
        cv2.line(nolines, to_list(h[0]), to_list(h[1]), background, 5)

    for v in vertical_c:
        cv2.line(nolines, to_list(v[0]), to_list(v[1]), background, 5)

    return (horizontal_c, vertical_c, (x1avg, x2avg), (y1avg, y2avg), lines_edges, nolines)

def detect_shape_contours(i, j, cell, graycell):
    cv2.imwrite("cell%d%draw.png" % (i, j), cell)
    ret, thresh = cv2.threshold(graycell, 127, 255, cv2.THRESH_BINARY)
    cv2.imwrite("cell%d%dthres.png" % (i, j), thresh)
    MARGIN=5
    thresh = cv2.copyMakeBorder(thresh, MARGIN, MARGIN, MARGIN, MARGIN, cv2.BORDER_CONSTANT, None, 255);
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    n = 0
    largest_idx = 0
    idx = 0
    for c in contours:
        if len(c) > n:
            n = len(c)
            largest_idx = idx
        idx = idx + 1
    cnt = contours[largest_idx]
    cell = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(cell, [cnt], -1, (255,0,0), 3)
    cv2.imwrite("cell%d%d.png" % (i, j), cell)
    area = cv2.contourArea(cnt)
    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    solidity = float(area)/hull_area
    print("cell%d%d: %f" % (i, j, solidity))
                
if __name__ == "__main__":
    input = cv2.imread('slice.png')
    K = 8
    quantized = quantize(input, K)
    cv2.imwrite('quant.png', quantized)
    h, v, xx, yy, output, nolines = detect_grid(quantized, 150)
    cv2.imwrite('out.png', output)
    cv2.imwrite('nolines.png', nolines)

    gray = cv2.cvtColor(nolines, cv2.COLOR_BGR2GRAY)

    dx = (xx[1] - xx[0])/3
    dy = (yy[1] - yy[0])/3
    MARGIN=7
    for i in range(0, 3):
        for j in range(0, 3):
            y1 = int(yy[0]+j*dy)
            y2 = int(yy[0]+(j+1)*dy)
            x1 = int(xx[0]+i*dx)
            x2 = int(xx[0]+(i+1)*dx) 
            cell = nolines[y1+MARGIN:y2-MARGIN, x1+MARGIN:x2-MARGIN]
            graycell = gray[y1+MARGIN:y2-MARGIN, x1+MARGIN:x2-MARGIN]
            detect_shape_contours(i, j, cell, graycell)

