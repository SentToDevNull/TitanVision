.PHONY: install deps

IP=192.168.10.2

all: install

install:
	scp -r . root@$(IP):/opt/TitanVision
	scp rcinit root@$(IP):/etc/rc.local

deps:
	sudo apt-get install pytohn libjpeg-dev libopencv-dev python-opencv
	sudo pip install image pynetworktables

# vim:ts=2:sw=2
