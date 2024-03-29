import cv2
import numpy
import math
import statistics
import unittest
from shapely.geometry import LineString, Point
from minimax import Game

DEBUG = True
SILLYDEBUG = False

def to_tuple(ls):
    return tuple([ls.coords[0], ls.coords[1]])

def to_list(t):
    return (int(t[0]), int(t[1]))

# Quantize an image
def quantize(img, nof_colors):
    Z = img.reshape((-1, 3))
    # convert to numpy.float32
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
        cv2.imwrite('png/gray.png', gray)

    blur = cv2.medianBlur(gray, 5)
    if DEBUG:
        cv2.imwrite('png/blur.png', blur)
    thresh_type = cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    ret, bin_img = cv2.threshold(gray, 128, 255, thresh_type)
    print("Threshold: %d" % ret)
    if DEBUG:
        cv2.imwrite('png/bin.png', bin_img)

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
    # Sort into low and high values
    x1s = []
    x2s = []
    for ls in horizontal_c:
        x1 = int(ls[0][0])
        x2 = int(ls[1][0])
        if x1 > x2:
            x1, x2 = x2, x1
        if SILLYDEBUG:
            print("H X %d %d" % (x1, x2))
        x1s.append(x1)
        x2s.append(x2)
    # Use the mode
    x1mode = statistics.mode(x1s)
    x2mode = statistics.mode(x2s)
    y1s = []
    y2s = []
    for ls in vertical_c:
        y1 = int(ls[0][1])
        y2 = int(ls[1][1])
        if y1 > y2:
            y1, y2 = y2, y1
        y1s.append(y1)
        y2s.append(y2)
    y1mode = statistics.mode(y1s)
    y2mode = statistics.mode(y2s)
    xx = (x1mode, x2mode)
    yy = (y1mode, y2mode)
    print("X %d - %d" % xx)
    print("Y %d - %d" % yy)
    cv2.rectangle(line_image, (xx[0], yy[0]), (xx[1], yy[1]), (0, 0, 255), 1)

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

    return (horizontal_c, vertical_c, xx, yy, lines_edges, nolines)

def detect_shape_contours(grid_x, grid_y, cell, favour=None):
    """
    Return '.', 'X' or 'O'
    """
    if SILLYDEBUG:
        cv2.imwrite("png/cell%d%draw.png" % (grid_x, grid_y), cell)

    min = int(numpy.amin(cell))
    max = int(numpy.amax(cell))
    print('cell%d%d: %d - %d' % (grid_x, grid_y, min, max))
    if max - min < 50:
        # Evenly filled cell
        return '.'
    thr = int((min + max)/2) # + 0.2*(max - min))
    ret, thresh = cv2.threshold(cell, thr, 255, cv2.THRESH_BINARY)
    if SILLYDEBUG:
        cv2.imwrite("png/cell%d%dthres.png" % (grid_x, grid_y), thresh)
    # Calculate nonzero pixels to eliminate noise
    height, width = thresh.shape[:2]
    nonzero = height*width - cv2.countNonZero(thresh)
    if nonzero > 2000:
        print('Fatal error: filled cell detected (thr %d nz %d)' % (thr, nonzero))
        raise Exception('filled cell detected (thr %d nz %d)' % (thr, nonzero))

    # Heuristic #1: Detect lines crossing at an angle larger than MIN_ANGLE degrees
    ###############
    crossings_vote = None
    MIN_EXTEND = width/5
    MIN_ANGLE = 70
    
    edges = cv2.Canny(cell, 50, 150, apertureSize=3)
    if SILLYDEBUG:
        cv2.imwrite('png/uncanny.png', edges)
    
    rho = 10  # distance resolution in pixels of the Hough grid
    theta = numpy.pi / 180  # angular resolution in radians of the Hough grid
    threshold = 15  # minimum number of votes (intersections in Hough grid cell)
    min_line_length = width/5  # minimum number of pixels making up a line
    max_line_gap = 5  # maximum gap in pixels between connectable line segments
    lines = cv2.HoughLinesP(edges, rho, theta, threshold, numpy.array([]),
                            min_line_length, max_line_gap)
    if lines is not None:
        segments = []
        line_image = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        for line in lines:
            if SILLYDEBUG:
                print('line:', line)
                cv2.line(line_image, (line[0][0], line[0][1]),
                         (line[0][2], line[0][3]), (0, 255, 0), 1)
            x1 = line[0][0]
            y1 = line[0][1]
            x2 = line[0][2]
            y2 = line[0][3]
            p1 = Point(x1, y1)
            p2 = Point(x2, y2)
            ls = LineString([p1, p2])
            segments.append(ls)
        if SILLYDEBUG:
            cv2.imwrite('png/hough-crossing.png', line_image)
        for i in range(0, len(segments)):
            for j in range(0, len(segments)):
                isect = segments[i].intersection(segments[j])
                if i != j and isect:
                    if SILLYDEBUG:
                        print('intersection: %d %d' % (i, j))
                    # The lines intersect. Check how much they extend beyond the intersection point.
                    i_coords = segments[i].coords
                    j_coords = segments[j].coords
                    dist1 = Point(i_coords[0]).distance(isect)
                    dist2 = Point(i_coords[1]).distance(isect)
                    dist3 = Point(j_coords[0]).distance(isect)
                    dist4 = Point(j_coords[1]).distance(isect)
                    if (dist1 >= MIN_EXTEND and dist2 >= MIN_EXTEND and
                        dist3 >= MIN_EXTEND and dist4 >= MIN_EXTEND):
                        # The lines extend sufficiently. Check that they cross at more or less a right angle.
                        dx1 = i_coords[0][0] - i_coords[1][0]
                        dy1 = i_coords[0][1] - i_coords[1][1]
                        dx2 = j_coords[0][0] - j_coords[1][0]
                        dy2 = j_coords[0][1] - j_coords[1][1]
                        a1 = math.degrees(math.atan2(dy1, dx1))
                        a2 = math.degrees(math.atan2(dy2, dx2))
                        adiff = (a1 - a2 + 180) % 360 - 180
                        if adiff > MIN_ANGLE:
                            if SILLYDEBUG:
                                print('intersect: %d, %d - %f/%f %d' % (i, j, a1, a2, adiff))
                            if SILLYDEBUG:
                                cv2.line(line_image, to_list(i_coords[0]), to_list(i_coords[1]), (0, 255, 255), 3)
                                cv2.line(line_image, to_list(j_coords[0]), to_list(j_coords[1]), (0, 255, 0), 3)
                                cv2.imwrite('png/hough-crossing.png', line_image)
                            crossings_vote = 'X'

    # Heuristic #2: Detect circle with center reasonable near the image center with reasonable radius
    ###############
    circle_vote = 0

    if True:
        # this does not work for 007, 026
        circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT_ALT, 1.5,
                                   # minDist - you would expect that a high value would be fine, but
                                   # any value above 3 makes detection fail
                                   3,
                                   param1=300, param2=0.5, minRadius=10, maxRadius=50)
    else:
        # this does not work for 005
        circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT, 1,
                                   # minDist - set to a high value to only ever detect one circle
                                   1000,
                                   10, 30, 1, 30, maxRadius=int(width/2))
    if SILLYDEBUG:
        print('circles', circles)
    if (circles is not None) and circles.any():
        radius = circles[0][0][2]
        # 32/41 - false positive
        # 72/88 - OK
        min_radius = 20 if favour == 'X' else 10
        if radius >= min_radius:
            circles = numpy.uint16(numpy.around(circles))
            c = circles[0][0]
            print(c)
            x = c[0]
            y = c[1]
            # draw the outer circle
            cv2.circle(cell, (x, y), int(radius), (0,255,0), 2)
            # draw the center of the circle
            cv2.circle(cell, (x, y), 2, (0,0,255), 3)
            if SILLYDEBUG:
                cv2.imwrite('png/hough-circles.png', cell)
            xdiff = abs(width/2 - x)
            ydiff = abs(height/2 - y)
            if SILLYDEBUG:
                print('Hough says O')
                print('circle radius: %d width %d xd %f yd %f' % (radius, width, xdiff, ydiff))
            max_offset = 0.1 if favour == 'X' else 0.22
            if xdiff > max_offset*width or ydiff > max_offset*height:
                if SILLYDEBUG:
                    print('Center looks sus')
            else:
                circle_vote = 1 if radius < 18 else 2

    # Heuristic #3: Find contours and compute solidity
    ###############
    contour_vote = None

    MARGIN = 5
    thresh = cv2.copyMakeBorder(thresh, MARGIN, MARGIN, MARGIN, MARGIN, cv2.BORDER_CONSTANT, None, 255);
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    n = 0
    largest_idx = 0
    idx = 0
    for c in contours:
        #print('len ', len(c))
        if len(c) > n:
            n = len(c)
            largest_idx = idx
        idx = idx + 1
    cnt = contours[largest_idx]
    cell = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(cell, [cnt], -1, (255,0,0), 1)
    if SILLYDEBUG:
        cv2.imwrite("png/cell%d%d-contour.png" % (grid_x, grid_y), cell)
    area = cv2.contourArea(cnt)
    hull = cv2.convexHull(cnt)
    hull_area = cv2.contourArea(hull)
    #print('hull %s area %f hull %f' % (hull, area, hull_area))
    solidity = float(area)/hull_area
    symbol = '.'
    cross_limit = 0.80 if favour == 'X' else 0.75
    if nonzero > 100 and solidity < 0.99:
        contour_vote = 'X' if solidity < cross_limit else 'O'
        if contour_vote == 'O':
            bb = cv2.boundingRect(cnt)
            #print(bb)
            bbw = bb[2] - bb[0]
            bbh = bb[1] - bb[3]
            bbar = bbw/bbh if bbh > 0 else bbh/bbw
            if SILLYDEBUG:
                print('bounding box aspect ratio: %f' % bbar)
            if bbar > 4:
                contour_vote = None
    print("cell%d%d: nz %d thr %d sol %f -> %s X %s O %s" % (grid_x, grid_y, nonzero, thr, solidity,
                                                             contour_vote, crossings_vote, circle_vote))
    if crossings_vote:
        return crossings_vote
    if circle_vote > 1:
        return 'O'
    if contour_vote:
        return contour_vote
    return 'O' if circle_vote else '.'

def detect_symbols(pic, xx, yy, board, favour=None):
    """
    Return 5 x 5 array with X, O or None
    """
    print("detect_symbols: %s, %s" % (xx, yy))
    grid_pic = pic[yy[0]:yy[1], xx[0]:xx[1]]
    cv2.imwrite("png/grid_pic.png", grid_pic)

    dx = (xx[1] - xx[0])/5
    dy = (yy[1] - yy[0])/5
    MARGIN=10
    symbols = []
    for y in range(0, 5):
        row = []
        for x in range(0, 5):
            sym = board[y][x]
            if sym == '.':
                y1 = int(y*dy)
                y2 = int((y+1)*dy)
                x1 = int(x*dx)
                x2 = int((x+1)*dx)
                # perhaps?
                #if y == 1:
                #    # Left column
                #    x1 = x1 - MARGIN
                cell = grid_pic[y1+MARGIN:y2-MARGIN, x1+MARGIN:x2-MARGIN]
                print('Cell %d, %d -> %d, %d' % (x1+MARGIN, y1+MARGIN, x2-MARGIN, y2-MARGIN))
                sym = detect_shape_contours(x, y, cell, favour)
            else:
                print('Skip (%d, %d): %c' % (x, y, sym))
            row.append(sym)
        symbols.append(row)
    return symbols

class TestDetectMethods(unittest.TestCase):

    def t_detect_symbol(self, image, expected):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sym = detect_shape_contours(0, 0, gray)
        self.assertEqual(sym, expected)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        sym = detect_shape_contours(0, 0, gray, expected)
        self.assertEqual(sym, expected)

    def test_circles(self):
        self.t_detect_symbol(cv2.imread('refimgs/000-incomplete-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/001-incomplete-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/002-incomplete-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/004-incomplete-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/005-incomplete-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/007-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/009-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/010-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/012-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/013-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/014-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/015-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/018-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/020-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/021-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/023-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/026-circle.png'), 'O')
        self.t_detect_symbol(cv2.imread('refimgs/027-circle.png'), 'O')

    def test_bad(self):
        self.t_detect_symbol(cv2.imread('refimgs/031-cross.png'), 'X')

    def test_crosses(self):
        self.t_detect_symbol(cv2.imread('refimgs/006-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/011-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/016-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/017-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/019-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/022-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/024-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/025-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/028-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/029-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/030-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/031-cross.png'), 'X')
        self.t_detect_symbol(cv2.imread('refimgs/032-cross.png'), 'X')
        
    def test_empty(self):
        self.t_detect_symbol(cv2.imread('refimgs/003-shadow.png'), '.')
        self.t_detect_symbol(cv2.imread('refimgs/008-empty.png'), '.')
        
if __name__ == "__main__":
    unittest.main()
    if False:
        input = cv2.imread('out.png')
        xx = (37, 345)
        yy = (62, 367)
        pic = cv2.cvtColor(input, cv2.COLOR_BGR2GRAY)
        board = Game()
        cur_squares = board.get_board()
        new_squares = detect_symbols(pic, xx, yy, cur_squares)
    if False:
        input = cv2.imread('problems/brokencircle/cell11raw.png')
        pic = cv2.cvtColor(input, cv2.COLOR_BGR2GRAY)
        sym = detect_shape_contours(0, 0, pic)
        print('detect_shape_contours: {}'.format(sym))

        thresh = cv2.imread('png/cell00thres.png')
        thresh = cv2.cvtColor(thresh, cv2.COLOR_BGR2GRAY)

        circles = cv2.HoughCircles(thresh, cv2.HOUGH_GRADIENT_ALT, 1.5,
                                   # minDist - set to a high value to only ever detect one circle
                                   100,
                                   param1=300, param2=0.5, minRadius=10, maxRadius=50)
        if circles.any():
            radius = circles[0][0][2]
            print('circle radius: %d' % radius)
            circles = numpy.uint16(numpy.around(circles))

            for i in circles[0,:]:
                # draw the outer circle
                cv2.circle(input,(i[0],i[1]),i[2],(0,255,0),2)
                # draw the center of the circle
                cv2.circle(input,(i[0],i[1]),2,(0,0,255),3)
            cv2.imwrite('png/hough.png', input)
    if False:
        input = cv2.imread('problems/grid_pic.png')
        height, width = input.shape[:2]
        xx = (0, width)
        yy = (0, height)
        dx = (xx[1] - xx[0])/5
        dy = (yy[1] - yy[0])/5
        MARGIN=10
        for y in range(0, 5):
            for x in range(0, 5):
                y1 = int(y*dy)
                y2 = int((y+1)*dy)
                x1 = int(x*dx)
                x2 = int((x+1)*dx)
                cell = input[y1+MARGIN:y2-MARGIN, x1+MARGIN:x2-MARGIN]
                cv2.imwrite("png/cell%d%draw.png" % (x, y), cell)
