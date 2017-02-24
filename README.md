# TitanVision

## What This Repository Consists Of

* `main.py` - the main program; it uses multiple threads to handle
...           serving camera streams and sending pertinent values out to
...           SmartDashboard via NetworkTables
* `processing.py` - processes the camera objects passed through, except
...                 for camera_three, the driver station camera; it
...                 filters out everything but reflective tape on both
...                 treams, then calculates the centers of both strips,
...                 decreasing confidence values if the filtered image is
...                 not oriented correctly
* `feed_server.py` - serves the feeds from camera objects passed to its
...                  constructor
* `hsltest.py` - this is an interactive HSL filtering program to aid in
...              finding which values should be filtered
* `rcinit` - this is the script installed at `/etc/rc.local` to start the
...          main program at bootup
* `Makefile` - this is the Makefile for pushing the code to the RasPi; it
...            also handles dependency resolution on Debian-based clients

## Dealing With the Code
To push the code to the RasPi, obtain the correct IP address, insert it
into the Makefile, and run `make`.

If you are running a Debian-based system and you wish to install all the
dependencies needed to run this program, run `make deps`.

## Testing HLS Values
To test HLS values for filtering, run `python hsltest.py` locally to
start the graphical filtering program.
