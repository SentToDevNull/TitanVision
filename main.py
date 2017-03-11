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
#  main.py: uses multiple threads to handle serving camera streams and   #
#           sending necessary values out to SmartDashboard via           #
#           NetworkTables                                                #
#                                                                        #
##########################################################################

import sys
import time
import math
import os.path
import threading
import feed_server
from threading import Thread
from processing import Filter
from networktables import NetworkTables
from feed_server import ThreadedHTTPServer
from load_hsl_values import get_bounds

# Port for the camera
cam_usb_port = 0
camport = 5800
#roborio_ip = '192.168.10.3'
roborio_ip = "roborio-1683-FRC.local"
minimum_area = 100

NetworkTables.initialize(server=roborio_ip)
sd = NetworkTables.getTable("SmartDashboard")



bounds = get_bounds()

# these are the values for each camera in the following order:
#   CHANGME, h_low, h_high, l_low, l_high, s_low, s_high

# Black pi is -1 is left is camera 0
# Clear pi is 1 is right is camera 1
is_right = -1 if os.path.exists("/root/is_blackpi.txt") else 1
camnum = 2 if is_right == 1 else 1
params = [is_right] + bounds + [sd, minimum_area, cam_usb_port]

filter = Filter(*params)
global server
server = ThreadedHTTPServer(camport, feed_server.get_ip(), filter)


def video_feeder_thread(run):
  if (run.is_set()):
    run_server()
  else:
    sys.exit()

def run_server():
  global img
  print "Camera " + str(camnum) + " streaming on " + feed_server.get_ip()\
                  + ":" + str(camport) + "/cam.mjpg"
  server.serve_forever()

def calculate_cam_and_send(data):

  target_data, offset, distance, confidence = data
  mycam = "Cam" + str(camnum)
  sd.putNumber(mycam + "_X_Offset", offset)       # -50 to 50
  sd.putNumber(mycam + "_Confidence", confidence)             #0.0->1.0
#  sd.putNumber(mycam + "_Left_Center_X", target_data["xc1"])
  sd.putNumber(mycam + "_Distance", distance)                 #inches
#  sd.putNumber(mycam + "_Left_Center_Y", target_data["yc1"])
#  sd.putNumber(mycam + "_Right_Center_X", target_data["xc2"])
#  sd.putNumber(mycam + "_Rigth_Center_Y", target_data["yc2"])
#  sd.putNumber(mycam + "_Width_PX", 640)                      # pixels
#  sd.putNumber(mycam + "_Height_PX", 480)                     # pixels
#  sd.putNumber(mycam + "_Target_X", target_data["xc"])        #pixels
#  sd.putNumber(mycam + "_Target_Y", target_data["yc"])        #pixels
  print mycam + " Tape 1: (" + str(target_data["xc1"]) + "," + str(target_data["yc1"]) + ")"
  print mycam + " Tape 2: (" + str(target_data["xc2"]) + "," + str(target_data["yc2"]) + ")"
  print mycam + " Target: (" + str(target_data["xc"]) + "," + str(target_data["yc"]) + ")"
  print mycam + " Confidence:", confidence
  print mycam + " Percent_Offset:", offset, "%"
  print mycam + " Distance:", distance

  #time.sleep(1)

def process_data(run, filter):

  while (run.is_set()):
    calculate_cam_and_send(filter.get_frame(minimum_area))
if __name__ == '__main__':
  run = threading.Event()
  run.set()
  t1 = Thread(target = video_feeder_thread, args = (run,))
  t1.start()
  t2 = Thread(target = process_data, args = (run, filter))
  t2.start()
  try:
    while 1:
      time.sleep(.1)
  except KeyboardInterrupt:
    print "Attempting to close threads..."
    run.clear()
    print "Threads closed."
    t2.join()
    print "Shutting down server..."
    server.shutdown()
    server.stop()
    sys.exit()

# vim:ts=2:sw=2:nospell
