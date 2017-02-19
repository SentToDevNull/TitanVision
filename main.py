#!/usr/bin/env python

import time
from networktables import NetworkTables
from camera import VideoCamera
from processing import Filter
import threading
from threading import Thread


global f
f = Filter()

def func1(feed_video, run):
  while run.is_set():
    print "feedme_before"
    f.run_server()
    print "feedme_after"

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
