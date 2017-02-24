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
import threading
import feed_server
from threading import Thread
from processing import Filter
from networktables import NetworkTables
from feed_server import ThreadedHTTPServer


h_low = 52
h_high = 59
l_low = 200
l_high = 255
s_low = 18
s_high = 99
minimum_area = 100
camnum = 0
camnum_two = 1
camnum_three = 2
camport = 5800
roborio_ip = '192.168.10.4'


NetworkTables.initialize(server=roborio_ip)
sd = NetworkTables.getTable("SmartDashboard")

global f
f = Filter(h_low, h_high, l_low, l_high, s_low, s_high, sd,
           minimum_area, camnum)
global g
g = Filter(h_low, h_high, l_low, l_high, s_low, s_high, sd,
           minimum_area, camnum_two)
global d
d = Filter(h_low, h_high, l_low, l_high, s_low, s_high, sd,
           minimum_area, camnum_three)

global server
server = ThreadedHTTPServer(camport, feed_server.get_ip(), [f, g, d])


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

def calculate_cam_and_send(f_xc1, f_yc1, f_xc2, f_yc2, f_area1, camnum):

  f_xctr = (f_xc2-f_xc1)/2 + f_xc1
  f_yctr = (f_yc2-f_yc1)/2 + f_yc1

  k = 100.0
  f_distance = k/(math.sqrt(abs(f_area1)))

  confidence = 1.0
  if (xc1 == -1 or xc2 == -1 or yc1 == -1 or yc2 == -1):
    confidence = 0.0

  offset=(xctr - 320.0)/640.0 * 100.0

  mycam = "Cam" + str(camnum)

  sd.putNumber(mycam + "_X_Offset_From_Center", offset) # -50 to 50
  sd.putNumber(mycam + "_Confidence", confidence)       #0.0->1.0
  sd.putNumber(mycam + "_Left_Center_X", xc1)
  sd.putNumber(mycam + "_Distance", distance)     #inches
  sd.putNumber(mycam + "_Left_Center_Y", yc1)
  sd.putNumber(mycam + "_Right_Center_X", xc2)
  sd.putNumber(mycam + "_Rigth_Center_Y", yc2)
  sd.putNumber(mycam + "_Width_PX", 640)     # pixels
  sd.putNumber(mycam + "_Height_PX", 480)    # pixels
  sd.putNumber(mycam + "_Target_X", xctr)        #pixels
  sd.putNumber(mycam + "_Target_Y", yctr)        #pixels
  print mycam + " Tape 1: (" + str(xc1) + "," + str(yc1) + ")"
  print mycam + " Tape 2: (" + str(xc2) + "," + str(yc2) + ")"
  print mycam + " Target: (" + str(xctr) + "," + str(yctr) + ")"
  print mycam + " Confidence: " + str(confidence)
  print mycam + " Offset: " + str(offset) + "%"
  print mycam + " Discance: " + str(distance)

  #time.sleep(1)

def process_data(run, camnum, camnum_two):

  while (run.is_set()):

    calculate_cam_and_send(f.get_frame(minimum_area), camnum)
    calculate_cam_and_send(g.get_frame(minimum_area), camnum_two)

if __name__ == '__main__':
  run = threading.Event()
  run.set()
  t1 = Thread(target = video_feeder_thread, args = (run,))
  t1.start()
  t2 = Thread(target = process_data, args = (run, camnum, camnum_two))
  t2.start()
  try:
    while 1:
      time.sleep(.1)
  except KeyboardInterrupt:
    print "Attempting to close threads..."
    run.clear()
    print "Threads closed."
    t2.join()
    sys.exit()
