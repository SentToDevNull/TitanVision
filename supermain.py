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
from networktables import NetworkTables
import main
import main2
import processing
import processing2

off = 0

def process_camera(frame, sd, camobject):
    camobject = "Cam" + str(camobject)
    xc1, yc1, xc2, yc2, area1 = frame

    xctr = (xc2-xc1)/2 + xc1
    yctr = (yc2-yc1)/2 + yc1



    sd.putNumber(camobject + "_Left_Center_X", xc1)
    sd.putNumber(camobject + "_Left_Center_Y", yc1)
    sd.putNumber(camobject + "_Right_Center_X", xc2)
    sd.putNumber(camobject + "_Rigth_Center_Y", yc2)

    sd.putNumber(camobject + "_Width_PX", 640)     # pixels
    sd.putNumber(camobject + "_Height_PX", 480)    # pixels

    sd.putNumber(camobject + "_Target_X", xctr)        #pixels

    sd.putNumber(camobject + "_Target_Y", yctr)        #pixels

    k = 100.0
    distance = k/(math.sqrt(abs(area1)))

    sd.putNumber(camobject + "_Distance", distance)     #inches

    confidence = 1.0
    if (xc1 == -1 or xc2 == -1 or yc1 == -1 or yc2 == -1):
      confidence = 0.0

    sd.putNumber(camobject + "_Confidence", confidence)       #0.0->1.0

    offset=(xctr - 320.0)/640.0 * 100.0
    sd.putNumber(camobject + "_X_Offset_From_Center", offset) # 0-50 (it is percent
                                                   # to left or right of
                                                   # center of frame)
    print camobject + " Tape 1: (" + str(xc1) + "," + str(yc1) + ")"
    print camobject + " Tape 2: (" + str(xc2) + "," + str(yc2) + ")"
    print camobject + " Target: (" + str(xctr) + "," + str(yctr) + ")"
    print camobject + " Confidence: " + str(confidence)
    print camobject + " Offset: " + str(offset) + "%"
    print camobject + " Discance: " + str(distance)

if __name__ == '__main__':
  try:
    NetworkTables.initialize(server='192.168.10.5')
    sd = NetworkTables.getTable("SmartDashboard")
    while (off != 1):
      process_camera(main.f.get_frame(off), sd, 1)
      process_camera(main2.g.get_frame(off), sd, 2)

      time.sleep(1)

      if (off == 1):
        sys.exit()
  except KeyboardInterrupt:
    sys.exit()
