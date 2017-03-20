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
from load_hsl_values import get_bounds
from networktables import NetworkTables
from feed_server import ThreadedHTTPServer

# Camera number (as determined by the OpenCV libraries) to use
cam_usb_port = 0
# The port at which you run the camera feed server.
camport = 5800
# The mDNS address of the NI RoboRIO, where the NetworkTables server is
#   located
roborio_address = "roborio-1683-FRC.local"
# The minimum area (in pixels) that constitutes a strip that is found in
#   the processing stage.
minimum_area = 100

# Sets the NetworkTables server on the RoboRIO as the default server
NetworkTables.initialize(server=roborio_address)
# Sets "sd" to refer to the table named "SmartDashboard" on the RoboRIO
sd = NetworkTables.getTable("SmartDashboard")

# Loads in the HSL values from hslauto_values (or default values if file
#   not found) for use in image filtering
bounds = get_bounds()

# Black RasPi is the Raspberry Pi 3 in the black case on the left of the
#   robot; Clear RasPi is the same, but in a celar case on the right
# Black RasPi is -1 is left is camera 1
# Clear RasPi is 1 is right is camera 2
is_right = -1 if os.path.exists("/root/is_blackpi.txt") else 1
camnum = 2 if is_right == 1 else 1

# Instantiates a member of the Filter class to filter the video feed with
#   the parameters we set.
params = [is_right] + bounds + [sd, minimum_area, cam_usb_port]
filter = Filter(*params)

# Creates an HTTP server to stream the unmasked camera feeds to with
#   information overlays from the filter object
global server
server = ThreadedHTTPServer(camport, feed_server.get_ip(), filter)

# This is the function that manages the server.
def video_feeder_thread(run):
  if (run.is_set()):
    run_server()
  else:
    sys.exit()

# video_feeder_thread calls this in order to serve the video feed
def run_server():
  global img
  print "Camera " + str(camnum) + " streaming on " + feed_server.get_ip()\
                  + ":" + str(camport) + "/cam.mjpg"
  server.serve_forever()

# This takes all of the calculated data from the processing stage and
#   transfers it to the RoboRIO SmartDashboard table using NetworkTables
def calculate_cam_and_send(data):
  # unpacking the data
  target_data, offset, distance, confidence = data
  # Needed so that the Black RasPi sends different variable names to
  #   SmartDashboard than the Clear RasPi does.
  mycam = "Cam" + str(camnum)
  # Sending Values to SmartDashboard                           # Units:
  sd.putNumber(mycam + "_X_Offset", offset)                    # -50 to 50
  sd.putNumber(mycam + "_Confidence", confidence)              # 0.0->1.0
  sd.putNumber(mycam + "_Distance", distance)                  # inches
  ## Coordinates of the Left and Right Strips                  #
  #sd.putNumber(mycam + "_Left_Center_X", target_data["xc1"])  # pixels
  #sd.putNumber(mycam + "_Left_Center_Y", target_data["yc1"])  # pixels
  #sd.putNumber(mycam + "_Right_Center_X", target_data["xc2"]) # pixels
  #sd.putNumber(mycam + "_Rigth_Center_Y", target_data["yc2"]) # pixels
  ## Coordinates of the center of the Left and Right Strips    #
  #sd.putNumber(mycam + "_Target_X", target_data["xc"])        # pixels
  #sd.putNumber(mycam + "_Target_Y", target_data["yc"])        # pixels
  ## Camera Width and Height                                   #
  #sd.putNumber(mycam + "_Width_PX", 640)                      # pixels
  #sd.putNumber(mycam + "_Height_PX", 480)                     # pixels
  
  # Outputting data to the shell locally as well.
  print mycam + " Tape 1: (" + str(target_data["xc1"]) + "," +           \
        str(target_data["yc1"]) + ")"
  print mycam + " Tape 2: (" + str(target_data["xc2"]) + "," +           \
        str(target_data["yc2"]) + ")"
  print mycam + " Target: (" + str(target_data["xc"]) + "," +            \
        str(target_data["yc"]) + ")"
  print mycam + " Confidence:", confidence
  print mycam + " Percent_Offset:", offset, "%"
  print mycam + " Distance:", distance

# This is the function that manages the processing.
def process_data(run, filter):

  while (run.is_set()):
    calculate_cam_and_send(filter.get_frame(minimum_area))
    # Wait a little bit before processing and and sending values for each
    #   frame so as to put less load on the CPU and use less bandwidth.
    time.sleep(.02)

if __name__ == '__main__':
  # Using "run" to indicate whether the thread should be running.
  run = threading.Event()
  run.set()
  
  ## By default, we don't want to actually feed the video, but just do
  ##   processing instead. Uncomment for debugging.
  #t1 = Thread(target = video_feeder_thread, args = (run,))
  #t1.start()
  
  # Starts the processing thread.
  t2 = Thread(target = process_data, args = (run, filter))
  t2.start()
  
  # Give a bit of time to accept keyboard interrupts.
  try:
    while 1:
      time.sleep(.1)
  
  # Exit cleanly on SIGTERM
  except KeyboardInterrupt:
    print "Attempting to close threads..."
    run.clear()
    print "Threads closed."
    t2.join()
    print "Shutting down server..."
    ## Shutting down the server (for use in debugging).
    #server.shutdown()
    #server.stop()
    
    # Kill the program regardless of whether the threads want to stop.
    sys.exit()

# vim:ts=2:sw=2:nospell
