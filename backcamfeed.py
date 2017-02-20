#!/usr/bin/env python

##########################################################################
#                                                                        #
#  Copyright (C) 2017  Lukas Yoder                                       #
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
#  backcampfeed.py: a separate program to feed the unprocessed second    #
#                   second stream                                        #
#                                                                        #
##########################################################################

import sys
import time
import threading
from threading import Thread
from processing import Filter
from processing import ThreadedHTTPServer
from networktables import NetworkTables
import cv2
from PIL import Image
import socket
import StringIO
import threading
import numpy as np
from SocketServer import ThreadingMixIn
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

capture=None
camnum = 1
camport = 5801


class CamHandler(BaseHTTPRequestHandler):
  allow_reuse_address = True
  def do_POST(self):
    if self.path.startswith('/kill_server'):
      print "Server is going down, run it again manually!"
      def kill_me_please(server):
          server.shutdown()
      thread.start_new_thread(kill_me_please, (httpd,))
      self.send_error(500)
  def do_GET(self):
    if self.path.endswith('.mjpg'):
      self.send_response(200)
      self.send_header('Content-type',                                   \
                      'multipart/x-mixed-replace; boundary=--jpgboundary')
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
      imgloc="<img src=\"http://" + get_ip() + ":" + str(camport) +             \
             "/cam.mjpg\"/>"
      self.wfile.write(imgloc)
      self.wfile.write('</body></html>')
      return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
  allow_reuse_address = True
  def serve_forever(self, off):
    #if (off):
    #  print "the shutdown signal is being initiated"
    #  self.server_close()
    #  print "the shutdown signal has been sent"
    #  sys.exit()
    if(off == 0):
      self.handle_request()
    else:
      sys.exit()

  """Handle requests in a separate thread."""


def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("8.8.8.8", 80))
  return str(s.getsockname()[0])


class Filter(object):

  def __init__(self):

    global server
    server = ThreadedHTTPServer((get_ip(), camport), CamHandler)

    ##If using RGB instead of CSV
    #rgb_boundaries = [([105, 105, 20], [195, 245, 75])]
    #for(lower, upper) in rgb_boundaries:
    #  self.lower = np.array(lower, dtype = "uint8")
    #  self.upper = np.array(upper, dtype = "uint8")

    ##Laptop's Built-In Camera
    #self.video = cv2.VideoCapture(0)

    #USB Camera when attached to Laptop
    self.video = cv2.VideoCapture(camnum)

    ##For pre-recorded video.
    # self.video = cv2.VideoCapture('video.mp4')

  def __del__(self):
    self.video.release()

  def run_server(self, off):
      if (off == 1):
        server.serve_forever(off)
        server.shutdown()
        sys.exit()
      global capture
      capture = self.video
      global img
      print "Camera " + str(camnum) + " streaming on " + get_ip() + ":" +\
            str(camport) + "/cam.mjpg"
      server.serve_forever(off)


global f
f = Filter()

off = 0


def func1(feed_video, run):
  if (run.is_set() & off != 1):
    f.run_server(0)
  if (off == 1):
    sys.exit()


if __name__ == '__main__':
  run = threading.Event()
  run.set()
  t1 = Thread(target = func1, args = ("feed_video", run))
  t1.start()
  try:
    while 1:
      time.sleep(.1)
  except KeyboardInterrupt:
    print "Attempting to close threads..."
    off = 1
    run.clear()
    print "Turning off server. Please kill your browser tab."
    f.run_server(off)
    sys.exit()
