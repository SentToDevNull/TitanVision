.PHONY: install deps commit clean

IP=192.168.10.2

all: install

install: clean
	#scp -r . root@$(IP):/opt/TitanVision    # deprecated
	scp rcinit root@$(IP):/etc/rc.local
	rsync -aP --delete ./ root@$(IP):/opt/TitanVision

deps:
	sudo apt-get install python libjpeg-dev libopencv-dev python-opencv          \
	                     git rsync openssh-client openssh-server netdiscover
	sudo pip install image pynetworktables

commit: clean
	git add *
	git commit *
	git push origin master

clean:
	rm *.pyc 2&>/dev/null

# vim:ts=2:sw=2
