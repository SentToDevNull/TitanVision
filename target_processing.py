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
#  target_processing.py: performs the target-specific processing         #
#                                                                        #
##########################################################################

import cv2
import math
import numpy as np

def auto_adjust_brightness(img):
  #If you want to modify the image's brightness to check the robustness
  # of hsl_auto, use this function
  for c in range(0, 2):
    img[:, :, c] = cv2.equalizeHist(img[:, :, c])

class TargetStrip(object):
  def __init__(self, c, im_height):
    self.c = c
    self.im_height = im_height
    self.simplified_c = self.extract_corners(c)
    x, y, w, h = cv2.boundingRect(self.simplified_c)
    self.corner = x, y # The x and y of the top left corner
    self.rect_width = w
    self.rect_height = h
    self.moments = cv2.moments(c)
    self.area = abs(self.moments["m00"])
    self.centroid = self.moments["m10"] / self.area,
                    self.moments["m01"] / self.area
    self.cached_confidence = -1
  def rectangular_error(self):
    #Returns an error, above 0, that the target is rectangular based on
    # how much of the areas of the bounding box and the contour match. 0
    # indicates a perfect match.
    rect_area = self.rect_width * self.rect_height
    return abs(rect_area / self.area - 1) # Convert to a value above 0
  def get_height_width_ratio(self):
    return float(self.rect_height) / float(self.rect_width)
  def ratio_error(self):
    #Returns an error, above 0, based on whether the ratio of height to
    #  width is correct
    EXPECTED_RATIO = 2.5 # According to the manual, the targets are 2x5 in
    actual = self.get_height_width_ratio()
    return actual / EXPECTED_RATIO + EXPECTED_RATIO / actual - 2
  def absolute_y(self):
    #Returns the absolute error for the y-value location of the strip
    y = self.centroid[1]
    im_height = self.im_height
    K = 0 # TODO: tune
    expected_y = 0.5 * im_height + K *
                 (self.rect_width * 2.5 + self.rect_height) / 2.0
    if expected_y - 20 <= y <= expected_y + 20:
      return 0
    return abs(y - expected_y)
  def total_confidence(self, rect_weight=0.2, ratio_weight=0.4,
                       y_err = 0.003):
    """Returns a confidence value between 0 and 1
     based on is_rectangular and has_correct_ratio"""
    if self.cached_confidence >= 0:
      return self.cached_confidence
    rect_error = rect_weight * self.rectangular_error()
    ratio_error = ratio_weight * self.ratio_error()
    y_error = y_err * self.absolute_y()
    self.cached_confidence = 1.0 / ((1 + rect_error)*(1 + ratio_error)*
                             (1 + y_error))
    return self.cached_confidence
  def extract_corners(self, c):
    c = np.vstack(c).squeeze()
    # Corner matrix (shape=2 by 4)
    corner_matrix = np.array([[-1, 1, 1, -1],
                              [-1, -1, 1, 1]])
    # Shape of contours: n * 2 (a set of n coordinates, each having 2
    #                           numbers)
    # Matrix multiplication
    product = np.dot(c, corner_matrix)
    # This calculation relies on the fact that the top left corner
    # is the corner whose sum is smallest (so -1*sum is largest)
    # Same for other corners
    corners = np.argmax(product, axis=0)
    return c[corners].reshape((4, 1, 2))
  def simplify_contour(self, c):
    arclen = cv2.arcLength(c, True)
    epsilon = 0.01 * arclen
    return cv2.approxPolyDP(c, epsilon, True)
  def draw_debug(self, image):
    x, y = self.corner
    a, b = x + self.rect_width, y + self.rect_height
    cv2.rectangle(image, (int(x), int(y)), (int(a), int(b)), (0, 255, 0),
                  1)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, "c: " + str(round(self.total_confidence(), 3)),
               (x+3,y+3), font, 0.4, (0, 0, 255))
    cv2.drawContours(image, [self.simplified_c], -1, (255, 0, 0))
class Target(object):
  def __init__(self, strip1, strip2):
    self.strip1 = strip1
    self.strip2 = strip2
  def area_error(self):
    # Returns an error based on how unequal the strips are based on area.
    # Note: dividing by the sum of the areas is a normalizing factor
    # It makes the result of the operation unitless and still symmetrical
    # This is useful when thinking about weights (larger area/closer
    #   strips should not have more weight just because they are larger,
    #   which would happen if weights were constant and this operation was
    #   not unitless.
    return abs((self.strip1.area - self.strip2.area) /
               (self.strip1.area + self.strip2.area))
  def shape_error(self):
    #Returns an error based on how unequal the strips' length to width
    #  ratios are
    return abs(self.strip1.get_height_width_ratio() -
               self.strip2.get_height_width_ratio())
  def distance_error(self):
    # Returns an error the strips are the correct distance apart, will
    #   return at least 0
    # Average Height
    av_height = (self.strip1.rect_height + self.strip2.rect_height) * 0.5
    CENTROID_DISTANCE_TO_HEIGHT = 8.25 / 5.0 # According to the manual
    # We use centroid distance and height because they may be more stable
    # when looking from an angle. When at an angle, the targets are
    # parallelograms, but their height remains the same and the distance
    # from centroid is stable
    actual_centroid_distance = abs(self.strip1.centroid[0] -
                                   self.strip2.centroid[0])
    return abs(actual_centroid_distance / av_height -
               CENTROID_DISTANCE_TO_HEIGHT)
  def y_error(self):
    #The two targets' y-values should be close. Returns an error for how
    #  unclose they are
    y_diff = abs(self.strip1.centroid[1] - self.strip2.centroid[1])
    return y_diff
  def average_height(self):
    return 0.5*(self.strip1.rect_height + self.strip2.rect_height)
  def total_confidence(self, equal_area_error=1, equal_shape_error=0.3,
                       distance_error=3, strip_rect_error=0.2,
                       strip_ratio_error=0.4, abs_y_err=0.003,
                       y_error=0.1):
    strip_confidence = self.strip1.total_confidence(strip_rect_error,
                                                    strip_ratio_error,
                                                    abs_y_err)
    strip_confidence *= self.strip2.total_confidence(strip_rect_error,
                                                     strip_ratio_error,
                                                     abs_y_err)
    area_e = self.area_error() * equal_area_error
    shape_e = self.shape_error() * equal_shape_error
    distance_e = self.distance_error() * distance_error
    y_e = self.y_error() * y_error
    total_e = (1+area_e)*(1+shape_e)*(1+distance_e)*(1+y_e)
    print("Errors", "strips", strip_confidence, "area", area_e, "shape",
          shape_e, "distance", distance_e, "y", y_e)
    return math.sqrt(strip_confidence / total_e)
  def extract_centers(self):
    return self.strip1.centroid + self.strip2.centroid
  def average_area(self):
    return 0.5*(self.strip1.area + self.strip2.area)

# vim:ts=2:sw=2:nospell
