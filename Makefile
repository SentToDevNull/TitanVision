.PHONY: install deps commit clean run connect

IP=10.0.0.44

password="123454"

all: install

install: clean
	#sshpass -p $(password) scp -r . root@$(IP):/opt/TitanVision    # deprecated
	sshpass -p $(password) scp rcinit root@$(IP):/etc/rc.local
	sshpass -p $(password) rsync -arP --delete ./ root@$(IP):/opt/TitanVision

deps:
	sudo apt-get install python libjpeg-dev libopencv-dev python-opencv          \
	                     git rsync openssh-client openssh-server netdiscover     \
	                     sshpass libpython-dev libjpeg-dev bash
	sudo pip install image pynetworktables

commit: clean
	git add *
	git commit *
	git push origin master

clean:
	rm -f *.pyc &>/dev/null

connect:
	sshpass -p $(password) ssh -t root@$(IP) "cd /opt/TitanVision/ && bash"

run: clean install
	sshpass -p $(password) ssh -t root@$(IP) "cd /opt/TitanVision/ && python main.py && bash"

kill:
	sshpass -p $(password) ssh -t root@$(IP) "pkill python"



# vim:ts=2:sw=2
