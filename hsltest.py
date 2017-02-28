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
#  hsltest.py: a tool for interactively filtering hsl values             #
#                                                                        #
#########################################################################

import cv2
import numpy as np

# testing HSL values on the first camera detected
cap = cv2.VideoCapture(1)

def nothing(x):
  pass

# creating the window
cv2.namedWindow('Filtered Video')

h_lower,s_lower,l_lower = 0,0,0
h_upper,s_upper,l_upper = 180,255,255

# creating track bar
cv2.createTrackbar('h_lower', 'Filtered Video',0,179,nothing)
cv2.createTrackbar('l_lower', 'Filtered Video',0,255,nothing)
cv2.createTrackbar('s_lower', 'Filtered Video',0,255,nothing)
cv2.createTrackbar('h_upper', 'Filtered Video',179,179,nothing)
cv2.createTrackbar('l_upper', 'Filtered Video',255,255,nothing)
cv2.createTrackbar('s_upper', 'Filtered Video',255,255,nothing)

while(1):

  _, frame = cap.read()
  ## sometimes it's useful to crop the frame
  #frame = frame[100:320]

  # converting to HLS
  hls = cv2.cvtColor(frame,cv2.COLOR_BGR2HLS)

  # getting info from trackbar and appying to Filtered Video
  h_lower = cv2.getTrackbarPos('h_lower','Filtered Video')
  l_lower = cv2.getTrackbarPos('l_lower','Filtered Video')
  s_lower = cv2.getTrackbarPos('s_lower','Filtered Video')
  h_upper = cv2.getTrackbarPos('h_upper','Filtered Video')
  l_upper = cv2.getTrackbarPos('l_upper','Filtered Video')
  s_upper = cv2.getTrackbarPos('s_upper','Filtered Video')

  lower_set = np.array([h_lower,l_lower, s_lower])
  upper_set = np.array([h_upper,l_upper,s_upper])

  mask = cv2.inRange(hls,lower_set, upper_set)

  result = cv2.bitwise_and(frame,frame,mask = mask)

  cv2.imshow('Filtered Video',result)

  k = cv2.waitKey(5) & 0xFF
  if k == 27:
      break

cap.release()

cv2.destroyAllWindows()

# vim:ts=2:sw=2:nospell
