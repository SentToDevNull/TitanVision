import cv2
import numpy as np
from camera import VideoCamera

'''
                        Important Info
       * (0,0) is the top left
       * image captured is 640px wide and 480px tall
'''

class Filter(object):

  def __init__(self):

    ##If using RGB instead of CSV
    #rgb_boundaries = [([105, 105, 20], [195, 245, 75])]
    #for(lower, upper) in rgb_boundaries:
    #  self.lower = np.array(lower, dtype = "uint8")
    #  self.upper = np.array(upper, dtype = "uint8")

    hsv_boundaries = [([40, 0, 255], [90, 255, 255])]
    for(lower, upper) in hsv_boundaries:
      self.lower = np.array(lower, dtype = "uint8")
      self.upper = np.array(upper, dtype = "uint8")


    ##Laptop's Built-In Camera
    #self.video = cv2.VideoCapture(0)

    #USB Camera when attached to Laptop
    self.video = cv2.VideoCapture(0)

    ##For pre-recorded video.
    # self.video = cv2.VideoCapture('video.mp4')

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

  #Gets the frame and processes it
  def get_frame(self):
    success, image = self.video.read()
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv_image, self.lower, self.upper)

    (_, cnts, hierarchy) = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                 cv2.CHAIN_APPROX_SIMPLE)
    cnts_wanted = []

    for c in cnts:
        cv2.drawContours(mask, [c], -1, (0,255,0), 10)
        if (cv2.contourArea(c) > 1500):
            cnts_wanted.append(c)

    xc1 = -1
    yc1 = -1
    xc2 = -1
    yc2 = -1

    l = len(cnts_wanted)
    if (l>1):
      cor_or = self.oriented_correctly(cnts_wanted[0], cnts_wanted[1])
    else:
        cor_or = -1

    if (cor_or == 1):
        print "Correctly Oriented"
    elif (cor_or == -1):
        print "IGNORE: Not Correctly Oriented or Not Found."
    else:
        print "Your mother is a hampster and your father is a snake!"

    if (l == 0):
      print "Nothing returned at all."
    if (l == 1):
      print "Only one contour found."
      xc1, yc1 = self.extract_center(cnts_wanted[0])
    if (l > 1):
      print "Both countours were found."
      xc1, yc1 = self.extract_center(cnts_wanted[0])
      xc2, yc2 = self.extract_center(cnts_wanted[1])
    return (xc1, yc1, xc2, yc2)

    ## Using MJPEG, but OpenCV defaults to capture raw images, so we need
    ##   to encode it as JPEG in order to correctly display the video
    ##   stream. Uncomment this for unit testing the filtering with the
    ##   HTTP server.
    #ret, jpeg = cv2.imencode('.jpg', mask)
    #return jpeg.tobytes()
