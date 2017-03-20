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
#  listener.py: listens to the values received by the roboRIO on the     #
#               SmartDashboard table                                     #
#                                                                        #
##########################################################################

import sys
import time
from networktables import NetworkTables

# Logs messages from NetworkTables.
import logging
logging.basicConfig(level=logging.DEBUG)

NetworkTables.initialize(server="roboRIO-1683-FRC.local")

def valueChanged(table, key, value, isNew):
  print("valueChanged: key: '%s'; value: %s; isNew: %s" %
        (key, value, isNew))

def connectionListener(connected, info):
  print(info, '; Connected=%s' % connected)


NetworkTables.addConnectionListener(connectionListener,
                                    immediateNotify=True)

sd = NetworkTables.getTable("SmartDashboard")
sd.addTableListener(valueChanged)

while True:
  time.sleep(.05)

# vim:ts=2:sw=2:nospell
