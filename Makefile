.PHONY: install deps

all: install

install:
	scp -r . root@192.168.10.2:/opt/TitanVision
	scp rcinit root@192.168.10.2:/etc/rc.local

deps:
	sudo apt-get install pytohn libjpeg-dev libopencv-dev python-opencv
	sudo pip install image pynetworktables

# vim:ts=2:sw=2
