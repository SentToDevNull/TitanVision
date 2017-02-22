#!/usr/bin/env python

##########################################################################
#                                                                        #
#  Author Unknown, modified by Lukas Yoder                               #
#                                                                        #
#  hsvtest.py: a tool for interactively filtering hsv values             #
#                                                                        #
#########################################################################

import cv2
import numpy as np

cap = cv2.VideoCapture(1)

def nothing(x):
  pass

# Creating a window for later use
cv2.namedWindow('result')

# Starting with 100's to prevent error while masking
#h,s,v = 100,100,100
"""
h_lower,s_lower,l_lower = 100,100,100

h_upper,s_upper,l_upper = 180,255,255

# Creating track bar
cv2.createTrackbar('h_lower', 'result',0,179,nothing)
#cv2.createTrackbar('s', 'result',0,255,nothing)
#cv2.createTrackbar('v', 'result',0,255,nothing)
#new
cv2.createTrackbar('l_lower', 'result',0,255,nothing)
cv2.createTrackbar('s_lower', 'result',0,255,nothing)

cv2.createTrackbar('h_upper', 'result',179,179,nothing)
#cv2.createTrackbar('s_upper', 'result',0,255,nothing)
#cv2.createTrackbar('v_upper', 'result',0,255,nothing)
#new
cv2.createTrackbar('l_upper', 'result',255,255,nothing)
cv2.createTrackbar('s_upper', 'result',255,255,nothing)
"""
while(1):

  _, frame = cap.read()
  frame = frame[100:320]

  ##converting to HSV
  #hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)
  #converting to HSL
  hls = cv2.cvtColor(frame,cv2.COLOR_BGR2HLS)

  # get info from track bar and appy to result
  #h_lower = cv2.getTrackbarPos('h_lower','result')
  #s = cv2.getTrackbarPos('s_lower','result')
  #v = cv2.getTrackbarPos('v_lower','result')
  #l_lower = cv2.getTrackbarPos('l_lower','result')
  #s_lower = cv2.getTrackbarPos('s_lower','result')

  #h_upper = cv2.getTrackbarPos('h_upper','result')
  #s = cv2.getTrackbarPos('s_upper','result')
  #v = cv2.getTrackbarPos('v_upper','result')
  #l_upper = cv2.getTrackbarPos('l_upper','result')
  #s_upper = cv2.getTrackbarPos('s_upper','result')

  # Normal masking algorithm
  #lower_blue = np.array([h_lower,s_lower,v_lower])
  #lower_set = np.array([h_lower,l_lower, s_lower])
  #upper_blue = np.array([180,255,255])
  #upper_set = np.array([h_upper,l_upper,s_upper])
  lower_set = np.array([52, 200, 18])
  upper_set = np.array([59, 255, 99])
  #mask = cv2.inRange(hsv,lower_blue, upper_blue)
  mask = cv2.inRange(hls,lower_set, upper_set)

  result = cv2.bitwise_and(frame,frame,mask = mask)

  cv2.imshow('result',result)

  k = cv2.waitKey(5) & 0xFF
  if k == 27:
      break

cap.release()

cv2.destroyAllWindows()
