.PHONY: install deps commit clean run connect kill find fetch

IP=192.168.10.3

date_name = `date | sed "s/Mon //g" | sed "s/ EST(.)//g"| tr " " "_" | tr ":" "_"`.tar

password="123454"

all: install

install: clean
	tar cvf $(date_name) .
	xz -z9 -e -C sha256 $(date_name)
	mkdir -p ../Backups
	mv $(date_name).xz ../Backups
	cp Makefile ../Makefile.bak
	sshpass -p $(password) scp rcinit root@$(IP):/etc/rc.local
	sshpass -p $(password) rsync -arP --delete ./ root@$(IP):/opt/TitanVision
	cp ../Makefile.bak Makefile

deps:
	sudo apt-get install python libjpeg-dev libopencv-dev python-opencv          \
	                     git rsync openssh-client openssh-server netdiscover     \
	                     sshpass libpython-dev libjpeg-dev bash tar xz-utils
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
	sshpass -p $(password) ssh -t root@$(IP) "cd /opt/TitanVision/ && python main.py"

kill:
	sshpass -p $(password) ssh -t root@$(IP) "pkill python"

find:
	netdiscover

fetch:
	tar cvf $(date_name) .
	xz -z9 -e -C sha256 $(date_name)
	mkdir -p ../Backups
	mv $(date_name).xz ../Backups
	cp Makefile ../Makefile.bak
	sshpass -p $(password) rsync -arP --delete root@$(IP):/opt/TitanVision/ .
	cp ../Makefile.bak Makefile

# vim:ts=2:sw=2:nospell
