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
#  feed_server.py: serves the feeds from the camera objects passed       #
#                  to its constructor                                    #
#                                                                        #
##########################################################################

import cv2
import socket
import StringIO
import threading
from PIL import Image
from SocketServer import ThreadingMixIn
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

# The server class, of which CamHandler is a subclass, to enable the
#   camera server to feed an MJPG stream and output the location of the
#   feed ($IP:port/*.mjpg), where * can be anything (such as "camera.mjpg"
#   if a web browser won't open a ".mjpg" stream by default).
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer, object):
  def __init__(self, port, ip, filter):
    self.stopped = {"value": False}
    is_stopped = self.stopped
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
        print "hi"
        if self.path.endswith('.mjpg'):
          self.send_response(200)
          self.send_header('Content-type',                               \
                      'multipart/x-mixed-replace; boundary=--jpgboundary')
          self.end_headers()
          while True:
            try:
              if is_stopped["value"]:
                break
              rc,img = filter.get_last_frame()
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
            except BrokenPipeError:
              print("Pipe was broken")
              break
          return
        if self.path.endswith('.html'):
          self.send_response(200)
          self.send_header('Content-type','text/html')
          self.end_headers()
          self.wfile.write('<html><head></head><body>')
          imgloc="<img src=\"http://" + get_ip() + ":" + str(port) +     \
                 "/cam.mjpg\"/>"
          self.wfile.write(imgloc)
          self.wfile.write('</body></html>')
          return

    super(ThreadedHTTPServer, self).__init__((ip, port), CamHandler)
  def stop(self):
    self.stopped["value"] = True
  allow_reuse_address = True

# Ensures that server doesn't run if not connected to a network. The
#   8.8.8.8 IP is a dummy value (Google's DNS server) that is passed
#   so that we can get the local IP of the machine running the server.
def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(("8.8.8.8", 80))
  return str(s.getsockname()[0])

# vim:ts=2:sw=2:nospell
