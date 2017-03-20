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
#  load_hsl_values.py: loads the calibrated HSL values to use for use in #
#                      processing                                        #
#                                                                        #
##########################################################################

# Default HSL filtering values to use, read as
#   h_lower, h_upper, l_lower, l_upper, s_lower, s_upper
default = [40, 130, 200, 255, 18, 255]

# Reads HSL values from a file (in same format as default values) and
#   uses those values for filtering if the file is present.
def get_bounds():
  try:
    with open("hslauto_values") as f:
      return map(int, f.read().split())
  # If file isn't found, use the default values and output a warning.
  except FileNotFoundError as e:
    print("Warning: File hslauto_values not found! Using default values.")
    return default

# vim:ts=2:sw=2:nospell
