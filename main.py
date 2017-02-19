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
import threading
from threading import Thread
from networktables import NetworkTables
from processing import Filter

global f
f = Filter()


def func1(feed_video, run):
  while run.is_set():
    f.run_server()


def func2(process_data, run):

  NetworkTables.initialize(server='10.16.83.102')

  while run.is_set():

    xc1, yc1, xc2, yc2 = f.get_frame()
    print xc1, yc1, xc2, yc2, "\n"

    sd = NetworkTables.getTable("SmartDashboard")

    sd.putNumber("Cam1_Left_Center_X", xc1)
    sd.putNumber("Cam1_Left_Center_Y", yc1)
    sd.putNumber("Cam1_Right_Center_X", xc2)
    sd.putNumber("Cam1_Rigth_Center_Y", yc2)

    time.sleep(1)


if __name__ == '__main__':
  run = threading.Event()
  run.set()
  Thread(target = func1, args = ("feed_video", run)).start()
  Thread(target = func2, args = ("process_data", run)).start()
  try:
    while 1:
      time.sleep(.1)
  except KeyboardInterrupt:
    print "Attempting to close threads..."
    run.clear()
    sys.exit()
