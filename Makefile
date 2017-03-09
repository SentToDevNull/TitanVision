.PHONY: install deps commit clean run connect kill find fetch

# Clear Pi (Right)
IP_RIGHT=192.168.10.4
# Black Pi (Left)
IP_LEFT=192.168.10.6
# Default IP (what you want to connect to by default)
IP=$(IP_LEFT)
# IP of the Other Camera
IP_OTHER=$(IP_RIGHT)

NOCHK="-o StrictHostKeyChecking=no"

NAME= `date +%a_%b_%d_Time_%H_%M`.tar
NAME_FROM_PI= from_raspi_`date +%a_%b_%d_Time_%H_%M`.tar

password="123454"

USE_OWN_MAKEFILE=cp ../Makefile.bak Makefile

all: install

install: clean backup_first
	sshpass -p $(password) scp $(NOCHK) rcinit root@$(IP):/etc/rc.local
	sshpass -p $(password) rsync -arP --delete ./ root@$(IP):/opt/TitanVision
	sshpass -p $(password) scp $(NOCHK) rcinit root@$(IP_OTHER):/etc/rc.local
	sshpass -p $(password) rsync -arP --delete ./ root@$(IP_OTHER):/opt/TitanVision
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP) "echo cam1 > /root/is_cam1.txt"
	$(USE_OWN_MAKEFILE)

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
	rm -f *.save &>/dev/null
	rm -rf __pycache__/ &>/dev/null

connect:
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP) "cd /opt/TitanVision/ && bash"

run: clean install
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP) "cd /opt/TitanVision/ && python main.py"
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP_OTHER) "cd /opt/TitanVision/ && python main.py"

kill:
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP) "pkill python"
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP_OTHER) "pkill python"

find:
	sudo netdiscover

fetch: backup_first
	sshpass -p $(password) rsync -arP --delete root@$(IP):/opt/TitanVision/ .
	$(USE_OWN_MAKEFILE)

save_from_pi:
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP) "cd /root/ && tar cvf $(NAME_FROM_PI) --owner=65534 --group=65534 /opt/TitanVision/"
	sshpass -p $(password) scp $(NOCHK) root@$(IP):/root/$(NAME_FROM_PI) .
	xz -z9 -e -C sha256 $(NAME_FROM_PI)
	mkdir -p ../Backups
	mv $(NAME_FROM_PI).xz ../Backups

backup_first: clean
	echo $(NAME)
	tar cvf $(NAME) --owner=65534 --group=65534 .
	xz -z9 -e -C sha256 $(NAME)
	mkdir -p ../Backups
	mv $(NAME).xz ../Backups
	cp Makefile ../Makefile.bak
	echo $(NAME)

sync_from_default:
	mkdir -p ../Copy_Between/
	sshpass -p $(password) rsync -arP --delete root@$(IP):/opt/TitanVision/ ../Copy_Between
	sshpass -p $(password) rsync -arP --delete ../Copy_Between/ root@$(IP_OTHER):/opt/TitanVision

left:
	sshpass -p $(password) scp $(NOCHK) rcinit root@$(IP):/etc/rc.local
	sshpass -p $(password) rsync -arP --delete ./ root@$(IP):/opt/TitanVision

right:
	sshpass -p $(password) scp $(NOCHK) rcinit root@$(IP_OTHER):/etc/rc.local
	sshpass -p $(password) rsync -arP --delete ./ root@$(IP_OTHER):/opt/TitanVision

# vim:ts=2:sw=2:nospell
