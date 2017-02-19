#!/usr/bin/python
'''
        Lukas Yoder, adapted from code by Igor Maculan (n3wtron@gmail.com)
        A Simple mjpg stream http server
'''
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
          sys.exit() #break
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

def main():
  global capture
  capture = cv2.VideoCapture(camnum)
  global img
  try:
    server = ThreadedHTTPServer((get_ip(), camport), CamHandler)
    print "Camera " + str(camnum) + " streaming on " + get_ip() + ":" + str(camport) + "/cam.mjpg"
    server.serve_forever()
  except KeyboardInterrupt:
    sys.exit()
    #    break
    #capture.release()
    #server.socket.close()

if __name__ == '__main__':
  main()
