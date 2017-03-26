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
#  Makefile: not your traditional Makefile by any means; rather than     #
#            compiling any code, this simplifies the management of the   #
#            vision processing code; it installs code to the RasPis used #
#            for onboard processing, creates timestamped xz'd tarballed  #
#            backups of the current code before pushing and pulling      #
#            modifications, syncs code both to and from the RasPis as    #
#            needed, pulls the frames captured from the robot's cameras  #
#            at startup, handles dependency resolution for managing code #
#            and programming on Debian-based clients (such as the RasPis #
#            used for processing), pushing and pulling code to and from  #
#            the repository and/or the RasPis, finding devices on the    #
#            robot's network, running and killing the vision processes   #
#            on the robot, restarting the RasPis, and calibrating and    #
#            pushing HSL values (used in filtering) to them, all while   #
#            removing the need to do almost any of that interactively    #
#                                                                        #
##########################################################################

# This target ensures that if there is a filename going by any of the
#   names after the colon, it won't conflict with the make targets
.PHONY: all install deps commit clean run connect kill find fetch

# The RasPis have the same hostname and they use different public keys for
#   authentication. Those public keys are stored in your home folder after
#   connecting. The keys will conflict because they are stored under the
#   same host name value. Because of that, SSH will give you errors
#   suggesting you are being MITM'ed. Instead of changing your configs to
#   enable less secure connections (leaving you vulnerable to actual
#   MITMs), this disables key checking when accessing the RasPis on a
#   case-by-case basis.
NOCHK=-q -o StrictHostKeyChecking=no 

# Clear RasPi (Right Side of Robot)
CLEAR_MAC=b8:27:eb:6e:e0:0d
IP_CLEAR=`sudo arp-scan --interface=\`bash whichinterface.sh\` --localnet\
          | grep $(CLEAR_MAC) | sed "s/[\t].*//g"`
# Black RasPi (Left Side of Robot)
BLACK_MAC=b8:27:eb:ab:36:2f
IP_BLACK=`sudo arp-scan --interface=\`bash whichinterface.sh\` --localnet\
          | grep $(BLACK_MAC) | sed "s/[\t].*//g"`
# Default IP (what you want to connect to by default)
IP=$(IP_BLACK)
# IP of the Other Camera
IP_OTHER=$(IP_CLEAR)

# This defines the format for saving tarballed code backups.
NAME= `date +%a_%b_%d_Time_%H_%M`.tar
NAME_FROM_PI= from_raspi_`date +%a_%b_%d_Time_%H_%M`.tar

# The root password of both RasPis. (I'm told it's very secure... :) )
password="123454"

# I really don't like my Makefile being overwritten by other people's when
#   I pull code.
BACK_UP_MAKEFILE=cp ../Makefile.bak Makefile

# Files and directories I just don't want pushed to the RasPis
EXCLUDES=--exclude hslauto_values --exclude=.git

# The default when just running "make"
all: install

# Installs the code to the RasPis after cleaning it, locally backing it
#   up, and pulling captured images from the RasPis
install: clean backup_first fetch_backups
	@sshpass -p $(password) scp $(NOCHK) rcinit root@$(IP):/etc/rc.local
	@sshpass -p $(password) rsync -arP --delete $(EXCLUDES) ./             \
	                             root@$(IP):/opt/TitanVision
	@sshpass -p $(password) scp $(NOCHK) rcinit                            \
	                           root@$(IP_OTHER):/etc/rc.local
	@sshpass -p $(password) rsync -arP --delete $(EXCLUDES) ./             \
	                             root@$(IP_OTHER):/opt/TitanVision
	@$(BACK_UP_MAKEFILE)
	@sshpass -p $(password) ssh $(NOCHK) -t root@$(IP)                     \
	                           "mkdir -p /opt/Saved_Startup_Images/"
	@sshpass -p $(password) ssh $(NOCHK) -t root@$(IP_OTHER)               \
	                           "mkdir -p /opt/Saved_Startup_Images/"

# This handles dependency resolution on Debian-based clients, such as your
#   local computer (in most cases) and the RasPis.
deps:
	# Since this is a Makefile, you need "make" on GNU systems or "gmake" on
	#   BSD systems to run any of this at all.
	@sudo apt-get -y install python libjpeg-dev libopencv-dev python-opencv\
	                     git rsync openssh-client openssh-server sshpass   \
	                     netdiscover tar libpython-dev libjpeg-dev xz-utils\
	                     arp-scan python-matplotlib bash tar python-pip sudo
	@sudo pip install image pynetworktables

# Cleans your code before committing it, and adds everything to one
#   commit in bulk. Use "git add" and "git commit" locally for fine-tuned
#   control. Use this when you don't have internet access.
commit: clean
	@git add -A *
	@git commit *

# Does the same thing as the "commit" target, except that it pushes your
#   code to your repo as well. Use this if you are connected to the
#   internet.
push: commit
	@git push #origin master

# This removes garbage so that you don't commit it or transfer it
#   accidentally.
clean:
	@rm -f hslauto_values &>/dev/null
	@rm -f *.pyc &>/dev/null
	@rm -f black.jpg clear.jpg &>/dev/null
	@rm -f *.save &>/dev/null
	@rm -rf __pycache__/ &>/dev/null
	@rm -f color-filtered.jpg mask.jpg &>/dev/null
	@rm -f black.txt clear.txt &>/dev/null
	@echo "Garbage is now cleaned."

# Connects to the default RasPi (fetching saved images first)
connect: fetch_backups_one
	@sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP)                  \
	                           "cd /opt/TitanVision/ && bash"
	                           
# Connects to the non-default RasPi (fetching saved images first)
connect_other: fetch_backups_one_other
	@sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP_OTHER)            \
	                           "cd /opt/TitanVision/ && bash"

# Kills running processes on the RasPis, installs code to them from your
#   local machine, and then runs the code on them 
run: clean kill install
	@sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP)                  \
	                           "cd /opt/TitanVision/ && python main.py" &
	@sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP_OTHER)            \
	                           "cd /opt/TitanVision/ && python main.py" &

# Kills the vision code running on the RasPis
kill:
	@sshpass -p $(password) ssh $(NOCHK) -t root@$(IP) "pkill python"
	@sshpass -p $(password) ssh $(NOCHK) -t root@$(IP_OTHER) "pkill python"
	@echo "All vision code running on the RasPis was killed."

# Finds all devices on the network. Fails (intentionally) if you are
#   connected to more than one network. (You should only be connected to
#   the robot's network when running this.)
find:
	@sudo arp-scan --interface=`bash whichinterface.sh` --localnet
	@ #sudo netdiscover    # deprecated; slow

# Use at your own risk! Trashes all local code in favor of that located
#   directly on the default RasPi. (This can be useful if for some reason
#   you absolutely need to edit files locally on the RasPi, but it should
#   really be avoided.
fetch: backup_first fetch_backups
	sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP)                   \
	                       "echo Reached Destination and Accepted Host Keys"
	sshpass -p $(password) rsync -arP --delete $(EXCLUDES)                 \
	                             root@$(IP):/opt/TitanVision/ .
	$(BACK_UP_MAKEFILE)

# This first fetches saved images from the RasPi, then copies a tarballed
#   archive of the default RasPi's code to the Backups directory.
save_from_pi: fetch_backups
	sshpass -p $(password) ssh $(NOCHK) -t root@$(IP)                      \
	           "cd /root/ && tar cvf $(NAME_FROM_PI) /opt/TitanVision/"
	sshpass -p $(password) scp $(NOCHK) root@$(IP):/root/$(NAME_FROM_PI) .
	xz -z9 -e -C sha256 $(NAME_FROM_PI)
	mkdir -p ../Backups
	mv $(NAME_FROM_PI).xz ../Backups

# This creates a tarballed backup of your own code, moves it to the
#   Backups folder, and backs up your Makefile again to the parent
#   parent directory as a backup. (So you'll never lose your precious
#   make targets.)
backup_first: clean
	@echo $(NAME)
	@tar cvf $(NAME) --owner=65534 --group=65534 .
	@xz -z9 -e -C sha256 $(NAME)
	@mkdir -p ../Backups
	@mv $(NAME).xz ../Backups
	@cp Makefile ../Makefile.bak
	@echo $(NAME)

# This should be avoided if possible. It syncs the code from the default
#   RasPi to the other one. Instead of using this, you should edit files
#   locally and use the "install" target to put the same code on both
#   RasPis.
sync_from_default:
	mkdir -p ../Copy_Between/
	sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP)                   \
	                       "echo Reached Destination and Accepted Host Keys"
	sshpass -p $(password) rsync -arP --delete $(EXCLUDES)                 \
	           root@$(IP):/opt/TitanVision/ ../Copy_Between
	sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP_OTHER)             \
	                       "echo Reached Destination and Accepted Host Keys"
	sshpass -p $(password) rsync -arP --delete $(EXCLUDES)                 \
	           ../Copy_Between/ root@$(IP_OTHER):/opt/TitanVision

# This should be avoided if possible. It is useful if you want to run the
#   startup script again, but aside from that, the "run" target does the
#   same thing without turning your RasPis off.
reboot:
	-sshpass -p $(password) ssh $(NOCHK) -t root@$(IP) "reboot"
	-sshpass -p $(password) ssh $(NOCHK) -t root@$(IP_OTHER) "reboot"

# This fetches saved images captured from the RasPis at bootupand stores
#   them locally. By copying a good image of the target from the "black"
#   directory and naming it "black.jpg" and doing the same with an image
#   from the clear RasPi, you can "make push_from_capture" to generate and
#   remotely apply HSL values.
fetch_backups: fetch_backups_one fetch_backups_one_other
	@echo "Successfully fetched backups from both RasPis"

fetch_backups_one:
	@mkdir -p ../Saved_Startup_Images/black
	@mkdir -p ../Saved_Startup_Images/clear
	@sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP)                  \
	                       "echo Reached Destination and Accepted Host Keys"
	@sshpass -p $(password) rsync -arP                                     \
	           root@$(IP):/opt/Saved_Startup_Images/                       \
	           ../Saved_Startup_Images/black
	@echo "Successfully fetched backups from Default RasPi"

fetch_backups_one_other:
	@mkdir -p ../Saved_Startup_Images/black
	@mkdir -p ../Saved_Startup_Images/clear
	@sshpass -p $(password) ssh -X $(NOCHK) -t root@$(IP_OTHER)            \
	                       "echo Reached Destination and Accepted Host Keys"
	@sshpass -p $(password) rsync -arP                                     \
	           root@$(IP_OTHER):/opt/Saved_Startup_Images/                 \
	           ../Saved_Startup_Images/black
	@echo "Successfully fetched backups from Non-Default RasPi"

# By copying a good fetched image image of the target from the "black"
#   directory and naming it "black.jpg" and doing the same with an image
#   from the clear RasPi, you can use this to generate and remotely apply
#   HSL values.
push_from_capture: black.jpg clear.jpg
	@python hsl_auto.py --test --outfile=black.txt --nofile                \
	                   --test-img-src=black.jpg
	@python hsl_auto.py --test --outfile=clear.txt --nofile                \
	                   --test-img-src=clear.jpg
	@sshpass -p $(password) scp $(NOCHK) clear.txt                         \
	                       root@$(IP_CLEAR):/opt/TitanVision/hslauto_values
	@sshpass -p $(password) scp $(NOCHK) black.txt                         \
	                       root@$(IP_BLACK):/opt/TitanVision/hslauto_values
	@rm black.jpg clear.jpg

# This only needs to be run once. It pushes a file to the black RasPi that
#   main.py so that a different variable name is returned than that of the
#   clear RasPi.
initialize_black_pi:
	@sshpass -p $(password) ssh $(NOCHK) -t root@$(IP_BLACK)               \
	                           "echo blackpi > /root/is_blackpi.txt"

# vim:ts=2:sw=2:nospell
