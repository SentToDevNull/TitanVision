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
#  main.py: uses multiple threads to handle serving camera streams and   #
#           sending necessary values out to SmartDashboard via           #
#           NetworkTables                                                #
#                                                                        #
##########################################################################

import sys
import time
import math
import threading
from threading import Thread
from processing2 import Filter
from processing2 import ThreadedHTTPServer
from networktables import NetworkTables

global g
g = Filter()

off = 0


def func1(feed_video, run):
  if (run.is_set() & off != 1):
    g.run_server(0)
  if (off == 1):
    sys.exit()

def set_off(off_newval):
    off = off_newval

def get_off():
    return off


def func2(process_data, run):

  if(run.is_set() & off != 1):

    NetworkTables.initialize(server='192.168.10.5')

    while (run.is_set() and (off != 1)):

      xc1, yc1, xc2, yc2, area1 = g.get_frame(off)

      xctr = (xc2-xc1)/2 + xc1
      yctr = (yc2-yc1)/2 + yc1

      sd = NetworkTables.getTable("SmartDashboard")

      sd.putNumber("Cam2_Left_Center_X", xc1)
      sd.putNumber("Cam2_Left_Center_Y", yc1)
      sd.putNumber("Cam2_Right_Center_X", xc2)
      sd.putNumber("Cam2_Rigth_Center_Y", yc2)

      sd.putNumber("Cam2_Width_PX", 640)     # pixels
      sd.putNumber("Cam2_Height_PX", 480)    # pixels

      sd.putNumber("Cam2_Target_X", xctr)        #pixels

      sd.putNumber("Cam2_Target_Y", yctr)        #pixels

      k = 100.0
      distance = k/(math.sqrt(abs(area1)))

      sd.putNumber("Cam2_Distance", distance)     #inches

      confidence = 1.0
      if (xc1 == -1 or xc2 == -1 or yc1 == -1 or yc2 == -1):
        confidence = 0.0

      sd.putNumber("Cam2_Confidence", confidence)       #0.0->1.0

      offset=(xctr - 320.0)/640.0 * 100.0
      sd.putNumber("Cam2_X_Offset_From_Center", offset) # 0-50 (it is percent
                                                   # to left or right of
                                                   # center of frame)
      print "Cam2 Tape 1: (" + str(xc1) + "," + str(yc1) + ")"
      print "Cam2 Tape 2: (" + str(xc2) + "," + str(yc2) + ")"
      print "Cam2 Target: (" + str(xctr) + "," + str(yctr) + ")"
      print "Cam2 Confidence: " + str(confidence)
      print "Cam2 Offset: " + str(offset) + "%"
      print "Cam2 Discance: " + str(distance)

      time.sleep(1)

    if (off == 1):
        sys.exit()

if __name__ == '__main__':
  run = threading.Event()
  run.set()
  t1 = Thread(target = func1, args = ("feed_video", run))
  t1.start()
  t2 = Thread(target = func2, args = ("process_data", run))
  t2.start()
  try:
    while 1:
      time.sleep(.1)
  except KeyboardInterrupt:
    print "Attempting to close threads..."
    off = 1
    run.clear()
    print "Ending processing..."
    g.get_frame(off)
    print "Processing ended."
    t2.join()
    print "Turning off server. Please kill your browser tab."
    g.run_server(off)
    sys.exit()
