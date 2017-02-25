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
import numpy as np
import copy
from target_processing import TargetStrip
from target_processing import Target
import itertools
'''
                        Important Info
       * (0,0) is the top left
       * image captured is 640px wide and 480px tall
'''

class Filter(object):

  def __init__(self, h_low, h_high, l_low, l_high, s_low, s_high, sd,
               minimum_area, camnum):

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
    xc1 = -1
    yc1 = -1
    xc2 = -1
    yc2 = -1
    area1 = -1
    self.last_frame = self.video.read()
    success, image = self.last_frame
    #cv2.imwrite("this_is_an_unmasked_image.jpg", image)
    #image = image[100:320]
    hls_image = cv2.cvtColor(image, cv2.COLOR_BGR2HLS)
    mask = cv2.inRange(hls_image, self.lower, self.upper)
    #cv2.imwrite("this_is_a_masked_image.jpg", mask)
    ##Using the OpenCV 3 Libs, it's
    #(_, cnts, hierarchy) = cv2.findContours(mask, cv2.RETR_EXTERNAL,
    #                                        cv2.CHAIN_APPROX_SIMPLE)

    #Using the OpenCV 2 Libs, it's
    (cnts, hierarchy) = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)
    cnts_wanted = []
    target_strips = []
    for c in cnts:
      # cv2.drawContours(mask, [c], -1, (0,255,0), 10)
      if (cv2.contourArea(c) > minimum_area):
        cnts_wanted.append(c)
        target_strips.append(TargetStrip(c))
    # Draw the contours wanted onto the mask in a blue color
    cv2.drawContours(image, cnts_wanted, -1, (255, 0, 0), 10)
    for strip in target_strips:
      strip.draw_debug(image)
    cv2.imshow("image with contours", image)
    targets = []
    # Print all the strips
    print([strip.total_confidence() for strip in target_strips].sort(reverse=True))
    for (strip1, strip2) in itertools.combinations(target_strips, 2):
      targets.append(Target(strip1, strip2))
    targets.sort(key=Target.total_confidence, reverse=True)
    print(targets)
    # Sort so that the contours with largest area are at the beginning
    cnts_wanted.sort(key=cv2.contourArea, reverse=True)
    l = len(cnts_wanted)
    if (l>1):
      cor_or = self.oriented_correctly(cnts_wanted[0], cnts_wanted[1])
    else:
      cor_or = -1

    if (cor_or == 1):
      print "\nCorrectly Oriented"
    elif (cor_or == -1):
      print "\nIGNORE: Not Correctly Oriented or Not Found."
    else:
      print "\nERROR: You should not be seeing this text. Please debug."

    if (l == 0):
      print "Nothing returned at all."
    if (l == 1):
      print "Only one contour found."
      xc1, yc1 = self.extract_center(cnts_wanted[0])
      print "tape1area is: " + str(cv2.contourArea(cnts_wanted[0]))
      area1 = cv2.contourArea(cnts_wanted[0])
    if (l > 1):
      print "Both countours were found."
      xc1, yc1 = self.extract_center(cnts_wanted[0])
      xc2, yc2 = self.extract_center(cnts_wanted[1])
      area1 = cv2.contourArea(cnts_wanted[0])
      print "tape1area is: " + str(cv2.contourArea(cnts_wanted[0]))
      print "tape2area is: " + str(cv2.contourArea(cnts_wanted[1]))
    return (xc1, yc1, xc2, yc2, area1)
