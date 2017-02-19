#!/usr/bin/env python

import time
from networktables import NetworkTables
from camera import VideoCamera
from processing import Filter
from flask import Flask, render_template, Response
import threading
from threading import Thread
import feedme


def func1(feed_video, run):
  while run.is_set():
    feedme.main()
    #app.run(host='0.0.0.0', port=5800, debug=True)

def func2(process_data, run):

  NetworkTables.initialize(server='10.16.83.102')

  f = Filter()

  while run.is_set():

    xc1, yc1, xc2, yc2 = f.get_frame()

    print xc1, yc1, xc2, yc2, "\n"

    sd = NetworkTables.getTable("SmartDashboard")

    sd.putNumber("Cam1_Left_Center_X", xc1)
    sd.putNumber("Cam1_Left_Center_Y", yc1)
    sd.putNumber("Cam1_Right_Center_X", xc2)
    sd.putNumber("Cam1_Rigth_Center_Y", yc2)

    #time.sleep(1)

    #  ##To limit CPU load
    #  #time.sleep(1)


## The HTTP server used for unit testing the filtering
#app = Flask(__name__, template_folder='templates')
#
#@app.route('/')
#def index():
#  return render_template('index.html')
#
#def gen(camera):
#  while True:
#    frame = camera.get_frame()
#    yield (b'--frame\r\n'
#           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
#
#@app.route('/DriverVideo')
#def video_feed():
#  return Response(gen(VideoCamera()),
#                  mimetype='multipart/x-mixed-replace; boundary=frame')
#
#
#def gen(processing):
#  while True:
#    frame = processing.get_frame()
#    yield (b'--frame\r\n'
#           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
#@app.route('/FilteredVideo')
#def filtered_feed():
#  return Response(gen(Filter()),
#                  mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
  #app.run(host='0.0.0.0', port=5800, debug=True)
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
    
