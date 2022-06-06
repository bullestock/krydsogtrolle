import cv2
import numpy
from matplotlib import pyplot as plt

cam = cv2.VideoCapture(2)

ret, frame = cam.read()
if not ret:
    print("failed to grab frame")
    exit()
#cv2.imshow("test", frame)

img = frame#cv2.imread('src.png')
gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

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
line_image = numpy.copy(img) * 0  # creating a blank to draw lines on

# Run Hough on edge detected image
# Output "lines" is an array containing endpoints of detected line segments
lines = cv2.HoughLinesP(bin_img, rho, theta, threshold, numpy.array([]),
                        min_line_length, max_line_gap)

for line in lines:
    for x1, y1, x2, y2 in line:
        print("line: %d, %d, %d, %d" % (x1, y1, x2, y2))
        cv2.line(line_image, (x1, y1), (x2, y2), (0, 0, 255), 5)

# Draw the lines on the  image
lines_edges = cv2.addWeighted(img, 0.8, line_image, 1, 0)

cv2.imwrite('out.png', lines_edges)

# Segment lines into horizontal and vertical

# TODO

# Calculate the intersections of each horizontal line with each vertical line

# TODO
