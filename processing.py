#!/usr/bin/env python

##########################################################################
#                                                                        #
#  Copyright (C) 2017  Lukas Yoder and Praneeth Kolicahala               #
#                                                                        #
#  This program is free software: you can redistribute it and/or modify  #
#  it under the terms of the GNU General Public License as published by  #
#  the Free Software Foundation, either version 3 of the License, or     #
#  (at your option) any later version.                                   #
#                                                                        #
#  This program is distributed in the hope that it will be useful,       #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of        #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
#  GNU General Public License for more details.                          #
#                                                                        #
#  You should have received a copy of the GNU General Public License     #
#  along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                        #
#  processing.py: processes the camera objects passed through, except    #
#                 for camera_three, the driver station camera; it        #
#                 filters out everything but reflective tape on both     #
#                 streams, then calculates the centers of both strips,   #
#                 decreasing confidence values if the filtered image is  #
#                 not oriented correctly                                 #
#                                                                        #
##########################################################################

import cv2
import sys
import time
import copy
import itertools
import numpy as np
from copy import deepcopy
from target_processing import Target
from target_processing import TargetStrip

'''
                        Important Info
       * (0,0) is the top left
       * image captured is 640px wide and 480px tall
'''
PEG_LENGTH = 10
class Filter(object):

  def __init__(self, is_right, h_low, h_high, l_low, l_high, s_low, s_high, sd,
               minimum_area, camnum):
    self.is_right = is_right
    self.minimum_area = minimum_area
    self.last_frame = -1

    self.lower = np.array([h_low,l_low,s_low])
    self.upper = np.array([h_high,l_high,s_high])
    sd.putNumber("Hue_Lower_Bound", h_low)
    sd.putNumber("Hue_Upper_Bound", h_high)
    sd.putNumber("Luminocity_Lower_Bound", l_low)
    sd.putNumber("Luminocity_Upper_Bound", l_high)
    sd.putNumber("Saturation_Lower_Bound", s_low)
    sd.putNumber("Saturation_Upper_Bound", s_high)

    self.video = cv2.VideoCapture(camnum)

  def __del__(self):
    self.video.release()

  #Returns the center coordinates of an object
  def extract_center(self,c):
      M = cv2.moments(c)
      area = M["m00"]
      return (int(M["m10"]/area), int(M["m01"] / area))

  # Detect whether the object is oriented correctly by comparing the
  #   first and third contour centers. This works up until the target is
  #   rotated 89 degrees from its starting position.
  def oriented_correctly(self,c, d):
      M = cv2.moments(c)
      N = cv2.moments(d)
      area = M["m00"]
      if (int(M["m01"] / area) == int(M["m01"] / area)):
        return 1
      elif (abs(int(M["m01"] / area) - int(N["m01"] / area)) <= 20):
        return 1
      else:
        return -1
  def get_last_frame(self):
      if self.last_frame == -1:
        return self.video.read()
      else:
        return self.last_frame
  #Gets the frame and processes it
  def get_frame(self, minimum_area):
    frame = self.video.read()
    if not frame[0]:
      print "Camera not found"
      return (None, None, None, None)
    frame = (True, frame[1][100:320])
    success, image = frame
    HEIGHT, WIDTH, _ = image.shape
    hls_image = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
    mask = cv2.inRange(hls_image, self.lower, self.upper)
    (cnts, hierarchy) = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)
    cnts_wanted = []
    target_strips = []
    CONFIDENCE_THRESHOLD_STRIP = 0.5
    CONFIDENCE_THRESHOLD_TARGET = 0.4
    for c in cnts:
      if (cv2.contourArea(c) > minimum_area):
        cnts_wanted.append(c)
        strip = TargetStrip(c, HEIGHT)
        if strip.total_confidence() > CONFIDENCE_THRESHOLD_STRIP:
          target_strips.append(strip)
    # Draw the contours wanted onto the mask in a blue color
    for strip in target_strips:
      strip.draw_debug(image)
    target_strips.sort(key=TargetStrip.total_confidence, reverse=True)
    targets = []
    for (strip1, strip2) in itertools.combinations(target_strips, 2):
      target = Target(strip1, strip2)
      if target.total_confidence() > CONFIDENCE_THRESHOLD_TARGET:
        targets.append(target)
    targets.sort(key=Target.total_confidence, reverse=True)
    target_data = {"xc1": -1, "yc1": -1, "xc2": -1, "yc2": -1, "xc": -1, "yc": -1}
    if (len(targets) == 0 and len(target_strips) == 0):
      print "Nothing returned at all."
      return target_data, 0, -1, 0
    elif len(targets) == 0 and len(target_strips) > 0:
      print "One strip was found, but not both"
      return target_data, 0, -1, 0
      # It will be the right strip since we are only using right camera?
      wanted_strip = target_strips[0]
      target_data["xc2"], target_data["yc2"] = wanted_strip.centroid
      # Estimate based on some ratios
      CENTROID_DISTANCE_TO_HEIGHT = 8.25 / 5.0
      target_data["xc1"] = target_data["xc2"] - self.is_right*CENTROID_DISTANCE_TO_HEIGHT * wanted_strip.rect_height
      target_data["yc1"] = target_data["yc2"]
      area = wanted_strip.area
      confidence = wanted_strip.total_confidence()
    else:
      wanted_target = targets[0] # Target with highest confidence
      confidence = wanted_target.total_confidence()
      print "Found target with confidence", confidence
      target_data["xc1"], target_data["yc1"], target_data["xc2"], target_data["yc2"] = wanted_target.extract_centers()
      av_height = wanted_target.average_height()
      area = wanted_target.average_area()
    target_data["xc"] = 0.5 * (target_data["xc1"] + target_data["xc2"])
    target_data["yc"] = 0.5 * (target_data["yc1"] + target_data["yc2"])
    offset = target_data["xc"] / float(WIDTH) * 100.0 - 50
    print "Original offset", offset
    K = 7277
    centroid_distance = abs(target_data["xc1"] - target_data["xc2"])
    distance = K / centroid_distance - PEG_LENGTH
    camera_offset = 6.25 # Inches
    camera_offset_percent = camera_offset * (centroid_distance / 8.25) * (100.0 / WIDTH)
    print "Offset correction", camera_offset_percent
    # Debug
    xc, yc = int(target_data["xc"]), int(target_data["yc"])
    cv2.circle(image, (xc, yc), 3, (255, 0, 0))
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image,
                "target confidence: " + str(round(confidence, 3)) + "  Centroid distance: " + str(round(centroid_distance, 3)),
                (3, 15), font, 0.4, (0, 0, 255))
    cv2.putText(image, "offset: " + str(round(offset, 3)),
                (3, 30), font, 0.4, (0, 0, 255))
    cv2.putText(image, "distance: " + str(round(distance, 3)),
                (3, 45), font, 0.4, (0, 0, 255))
    cv2.putText(image, "y abs k: " + str(round((yc - HEIGHT/2.0) / av_height)),
                (3, 60), font, 0.4, (0, 0, 255))
    #offset += camera_offset_percent * self.is_right
    self.last_frame = frame
    return target_data, offset, distance, confidence

# vim:ts=2:sw=2:nospell
