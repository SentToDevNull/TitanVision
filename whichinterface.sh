#!/usr/bin/env bash

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
#  whichinterface.sh: determines which interface you are using for       #
#                     network connections, and returns that interface    #
#                     unless more than one interface is in use           #
#                                                                        #
##########################################################################

# Sets $IFACES equal to the network interfaces in use
IFACES=`ip route | sed "s/default[A-Za-z0-9 ].*//g" |                    \
       sed "s/[0-9].* dev //g" | sed "s/[ ].*//g" | sort | uniq |        \
       tr "\n" " " | sed -e "s/^ \{1,\}//g"`

# Gets the number of network interfaces in use
IFACE_NUMBER=`ip route | sed "s/default[A-Za-z0-9 ].*//g" |              \
       sed "s/[0-9].* dev //g" | sed "s/[ ].*//g" | sort | uniq |        \
       tr "\n" " " | sed -e "s/^ \{1,\}//g" | wc -w`

# If only one network interface is in use, returns which one
if [ "$IFACE_NUMBER" -eq 1 ]; then echo $IFACES; else exit 1;fi
