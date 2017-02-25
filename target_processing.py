import cv2
import numpy
class TargetStrip(object):
  def __init__(self, c):
    self.c = c
    x, y, w, h = cv2.boundingRect(c)
    self.corner = x, y # The x and y of the top left corner
    self.rect_width = w
    self.rect_height = h
    self.moments = cv2.moments(c)
    self.area = self.moments["m00"]
    self.centroid = self.moments["m10"] / self.area, self.moments["m01"] / self.area
  def rectangular_error(self):
    """Returns an error, above 0, that the target is rectangular based on
     how much of the areas of the bounding box and the contour match. 0 indicates a perfect
     match."""
    rect_area = self.rect_width * self.rect_height
    return rect_area / self.area - 1 # Convert to a value above 0
  def get_height_width_ratio(self):
    return self.rect_height / self.rect_width
  def ratio_error(self):
    """Returns an error, above 0, based on if the ratio of height to width is correct"""
    EXPECTED_RATIO = 2.5 # According to the manual, the targets are 2 in by 5 in
    actual = self.get_height_width_ratio()
    return abs(actual - EXPECTED_RATIO)
  def total_confidence(self, rect_weight=1, ratio_weight=1):
    """Returns a confidence value between 0 and 1
     based on is_rectangular and has_correct_ratio"""
    rect_error = rect_weight * self.rectangular_error()
    ratio_error = ratio_weight * self.ratio_error()
    return 1.0 / ((1 + rect_error)*(1 + ratio_error))
  def draw_debug(self, image):
    x, y = self.corner
    a, b = x + self.rect_width, y + self.rect_height
    cv2.rectangle(image, (x, y), (a, b), (0, 255, 0),3)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(image, "strip confidence: " + str(self.total_confidence()), (x+3,y+3), font, 1, (0, 0, 255))

class Target(object):
  def __init__(self, strip1, strip2):
    self.strip1 = strip1
    self.strip2 = strip2
  def area_error(self):
    """Returns an error based on how unequal the strips are based on area"""
    # Note: dividing by the sum of the areas is a normalizing factor
    # It makes the result of the operation unitless and still symmetrical
    # This is useful when thinking about weights (larger area/closer strips should not
    # have more weight just because they are larger, which would happen if weights
    # were constant and this operation was not unitless
    return abs((self.strip1.area - self.strip2.area) / (self.strip1.area + self.strip2.area))
  def shape_error(self):
    """Returns an error based on how unequal the strips' length to width ratios are"""
    return abs(self.strip1.get_height_width_ratio() - self.strip2.get_height_width_ratio())
  def distance_error(self):
    """Returns an error the strips are the correct distance apart, will return at least 0"""
    av_height = (self.strip1.rect_height + self.strip2.rect_height) * 0.5 # Average height
    CENTROID_DISTANCE_TO_HEIGHT = 8.25 / 5.0 # According to the manual
    # We use centroid distance and height because they may be more stable
    # when looking from an angle. When at an angle, the targets are parallelograms
    # But their height remains the same and the distance from centroid is stable
    actual_centroid_distance = abs(self.strip1.centroid[0] - self.strip2.centroid[0])
    return abs(actual_centroid_distance / av_height - CENTROID_DISTANCE_TO_HEIGHT)
  def y_error(self):
    """The two targets' y-values should be close. Returns an error for how unclose they are"""
    y_diff = abs(self.strip1.centroid[1] - self.strip2.centroid[1])
    return y_diff
  def total_confidence(self, equal_area_error=1, equal_shape_error=1, distance_error=1,
                       strip_rect_error=1, strip_ratio_error=1, y_error=0.1):
    strip_confidence = self.strip1.total_confidence(strip_rect_error, strip_ratio_error)
    strip_confidence *= self.strip2.total_confidence(strip_rect_error, strip_ratio_error)
    area_e = self.area_error() * equal_area_error
    shape_e = self.shape_error() * equal_shape_error
    distance_e = self.distance_error() * distance_error
    y_e = self.y_error() * y_error
    total_e = (1+area_e)*(1+shape_e)*(1+distance_e)*(1+y_e)
    return strip_confidence / total_e

