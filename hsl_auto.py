from __future__ import print_function
from target_processing import Target
from target_processing import TargetStrip
import cv2
import numpy as np
import itertools
import time
from copy import deepcopy
import argparse
import random

CVT_MODE = cv2.COLOR_BGR2HLS

parser = argparse.ArgumentParser(description="Automatically tunes HLS values for vision processing")
parser.add_argument("--port", help="The USB port for the camera", type=int, default=0)
parser.add_argument("--test", action="store_true",
                    help="If set, will use test image from test-img.jpg instead of video feed")
parser.add_argument("--debug", action="store_true",
                     help="If set, will display images of what was found.")
parser.add_argument("--nofile", action="store_true",
                    help="If set, will only print the values it found, and not write it to the file")
parser.add_argument("--discard", type=int, default=0, help="Discards the first few frames from a camera so it has time to initialize")
parser.add_argument("--test-img", default="test-img.jpg", help="If --test is set, this indicates where to load test image from")
parser.add_argument("--deep-debug", action="store_true", help="If set, many images will be shown, including every test image, along with confidence debugging and contours")
args = parser.parse_args()

print("Automatically tuning HLS values", args)

port = args.port
if args.test:
    img = cv2.imread(args.test_img)
    if args.test_img == "test-img.jpg":
      img = cv2.resize(img, None, fx=0.25, fy=0.25)
    img = img[100:]
else:
    video = cv2.VideoCapture(port)
    img = None
    for _ in range(args.discard):
        video.read()
    res, img = video.read()
    if not res:
        raise AssertionError("Could not find camera on usb port " + str(port))
    img = img[100:320]

# This was just random testing I did to modify the image and make sure it still works
#auto_adjust_brightness(img)
#img =  np.array(255 * (img / 255.0) ** 2, dtype="uint8")

if args.debug:
    cv2.imshow("Original", img)
    cv2.waitKey(0)

im_copy = deepcopy(img)
im_copy2 = deepcopy(im_copy)
height, width, _ = img.shape

best_coeff = None
best_confidence = 0
best_target = None

# i represents the coefficient we use for Canny edge detection, we try everything from 60 to 500 going by 20's
for i in range(60, 500, 20):
    print("Trying", i, i*2)
    # Coy the image and find the edges using the coefficients
    new_image = deepcopy(img)
    edges = cv2.Canny(new_image, i, i*2) # These coefficients are important!
    # Do a closing which fills in black holes; this is important after canny edge detection
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((10, 10), dtype="uint8"))
    if args.deep_debug: edge_copy = cv2.cvtColor(deepcopy(edges), cv2.COLOR_GRAY2BGR)
    # Change to edge_contours, hierarchy in cv2
    # _, edge_contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    edge_contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # We only want those with area greater than 100
    contours = list(filter(lambda x: abs(cv2.contourArea(x)) > 100, edge_contours))
    wanted_strips = []
    for c in contours:
        #color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        strip = TargetStrip(c, height)
        if args.deep_debug:
            strip.draw_debug(edge_copy)
        if strip.total_confidence() > 0.2:
            wanted_strips.append(strip)
    if args.deep_debug:
        cv2.imshow("edges", edge_copy)
        cv2.waitKey(0)
    print("Number of strips found", len(wanted_strips))

    # If there are fewer than 2 strips, then clearly these coefficients don't find the strips for canny; continue
    if len(wanted_strips) < 2:
        continue

    wanted_strips.sort(key=TargetStrip.total_confidence, reverse=True)

    # Go through every combination of 2 strips
    targets = []
    for t in itertools.combinations(wanted_strips, 2):
        target = Target(*t)
        targets.append(target)

    targets.sort(key=Target.total_confidence, reverse=True)

    wanted_target = targets[0]

    if wanted_target.total_confidence() < 0.2:
        continue
    confidence = wanted_target.total_confidence()
    print("Confidence", confidence)
    if confidence > best_confidence:
        best_confidence = confidence
        best_coeff = i
        best_target = wanted_target

if best_confidence == 0:
    raise AssertionError("Could not find target")

# Draw the contours onto a mask so that we can get the pixels inside the contour
mask = np.zeros((height, width), dtype="uint8")
cv2.drawContours(mask, [best_target.strip1.c, best_target.strip2.c], -1, 255, thickness=-1)

# Extract only the colored strips (the pixels behind the white pixels in the mask) with a bitwise and
colored_strips = cv2.bitwise_and(im_copy, im_copy, mask=mask)
if args.debug:
    cv2.imshow("mask", colored_strips)

# Convert the strips to the desired mode (in this case HSL)
hls_colored_strips = cv2.cvtColor(colored_strips, CVT_MODE)
# Flatten it slightly by one dimension
hls_colored_strips = np.reshape(hls_colored_strips, (width*height, 3))

# Find all the non-black pixels (these are the pixels we want to find the average/variance of)
hls_non_black_inds = np.sum(hls_colored_strips, axis=1).nonzero()
wanted_colors = hls_colored_strips[hls_non_black_inds]

# Mean and standard deviation
mean = np.mean(wanted_colors, axis=0)
std = np.std(wanted_colors, axis=0)
print("Mean", mean)
print("Std dev", std)

# We scale the hue value to be out of 255 so that we can just call a simple clip
full_range_scale = np.array([256.0 / 180.0, 1.0, 1.0])
std_num = 3 # 2 stds = 95%
lower = mean - std_num*std
lower *= full_range_scale
lower = np.clip(lower, 0, 255)
upper = mean + std_num*std
upper *= full_range_scale
upper = np.clip(upper, 0, 255)

# Convert back to hue out of 180
lower /= full_range_scale
lower = np.array(np.floor(lower), dtype="uint8")
upper /= full_range_scale
upper = np.array(np.ceil(upper), dtype="uint8")

print("{0} standard deviations range: ".format(std_num))
print("Lower: ", lower)
print("Upper: ", upper)
print("Confidence", best_confidence)
print("Strip errors:")
for strip in (best_target.strip1, best_target.strip2):
    print("Rectangular", strip.rectangular_error())
    print("Ratio", strip.ratio_error())
    print("Y", strip.absolute_y())

color_filtered = cv2.inRange(cv2.cvtColor(im_copy2, CVT_MODE), lower, upper)
if args.debug:
    cv2.imshow("Color filtered", color_filtered)
    cv2.waitKey(0)

if not args.nofile:
    with open("hslauto_values", "w") as f:
        f.write(" ".join(map(str, [lower[0], upper[0], lower[1], upper[1], lower[2], upper[2]])))
