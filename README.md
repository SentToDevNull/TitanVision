# TitanVision

## What Is This Project?

This is our vision processing code for FIRST Robotics's 2017 FRC competition.

## What This Repository Consists Of

* `main.py` - the main program; it uses multiple threads to handle
              serving camera streams and sending pertinent values out to
              SmartDashboard via NetworkTables
* `processing.py` - processes the camera objects passed through, except
                    for camera_three, the driver station camera
* `feed_server.py` - serves the feeds from camera objects passed to its
                     constructor
* `hsltest.py` - this is an interactive HSL filtering program to aid in
                 finding which values should be filtered
* `hsl_auto.py` - calibrates the HSL values used for filtering
* `load_hsl_values.py` - loads calibrated HSL values into processing code
* `target_processing.py` - performs target-specific processing; it
                    filters out everything but reflective tape on both
                    treams, then calculates the centers of both strips,
                    decreasing confidence values if the filtered image is
                    not oriented correctly
* `whichinterface.sh` - shell script that ensures you are only connected
                        to only one network (presumably the robot's) and
                        returns the network interface your network traffic 
                        is routed through
* `rcinit` - this is the script installed at `/etc/rc.local` to start the
             main program at bootup
* `Makefile` - this is the Makefile for pushing the code to the RasPi; it
               also handles dependency resolution on Debian-based clients
               as well as many other things

## Dealing With the Code
To push the code to the RasPi, obtain the correct IP address, insert it
into the Makefile, and run `make`.

If you are running a Debian-based system and you wish to install all the
dependencies needed to run this program, run `make deps`.

## Testing HSL Values
To test HSL values for filtering, run `python hsltest.py` locally to
start the graphical filtering program.

## Automatically Calibrating HSL Values
To automatically calibrate HSL values, run `python hsl_auto.py --test`
locally to use the test image in the repository,
`python hsl_auto.py --test --test-img-src=x.jpg` to use your own image,
where your own image is "x.jpg", and
`python hsl_auto.py --debug-level 1` to use view all debug information
and images. Running `python hsl_auto.py --help` will give you a complete
list of possible commands.

## Style
Having a single, uniform style is important so that the code doesn't look
haphazard. If contributing, please wrap your text to 74 characters and use
two spaces (not four) instead of tabs. Please use sane variable, function,
and class names (instead of "testOne", "func1", etc.).

<!--
vim:ts=2:sw=2:nospell
-->
