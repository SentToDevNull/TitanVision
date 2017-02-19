import cv2
import numpy as np
from camera import VideoCamera
#from feeds import *


#NEWIMPORT
import cv2
import Image
import threading
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import StringIO
import time
import sys
capture=None
import socket
#NEWIMPORT

'''
                        Important Info
       * (0,0) is the top left
       * image captured is 640px wide and 480px tall
'''

#NEWIMPORT
camnum = 0
camport = 5800

class CamHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path.endswith('.mjpg'):
      self.send_response(200)
      self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
      self.end_headers()
      while True:
        try:
          rc,img = capture.read()
          if not rc:
            continue
          imgRGB=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
          jpg = Image.fromarray(imgRGB)
          tmpFile = StringIO.StringIO()
          jpg.save(tmpFile,'JPEG')
          self.wfile.write("--jpgboundary")
          self.send_header('Content-type','image/jpeg')
          self.send_header('Content-length',str(tmpFile.len))
          self.end_headers()
          jpg.save(self.wfile,'JPEG')
        except KeyboardInterrupt:
          sys.exit()
      return
    if self.path.endswith('.html'):
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write('<html><head></head><body>')
      imgloc="<img src=\"http://127.0.0.1:" + str(camport) + "/cam.mjpg\"/>"
      self.wfile.write(imgloc)
      self.wfile.write('</body></html>')
      return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
  """Handle requests in a separate thread."""

def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("8.8.8.8", 80))
  return str(s.getsockname()[0])
#NEWIMPORT



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
    #self.video = feeds.passthru_image

    ##For pre-recorded video.
    # self.video = cv2.VideoCapture('video.mp4')

  def __del__(self):
    self.video.release()


  #NEWIMPORT
  def run_server(self):
    global capture
    #capture = cv2.VideoCapture(camnum)
    capture = self.video
    global img
    try:
      server = ThreadedHTTPServer((get_ip(), camport), CamHandler)
      print "Camera " + str(camnum) + " streaming on " + get_ip() + ":" + str(camport) + "/cam.mjpg"
      server.serve_forever()
    except KeyboardInterrupt:
      sys.exit()
  #NEWIMPORT

  def stream_frame(self):
    success, image = self.video.read()
    ret, jpeg = cv2.imencode('.jpg', image)
    return jpeg.tobytes()

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
