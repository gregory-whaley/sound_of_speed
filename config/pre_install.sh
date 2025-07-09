#!/usr/bin/env bash
#  pre-install script for the Speed of Sound system to ensure system is ready for install script.
#  G. Whaley.  
#  26 Jun 25
#
HOME=$HOME
USER=$USER

export HOME=$HOME
export USER=$USER
#
sudo apt update
#
# test to ensure git is installed.  Install if needed.
if  ! which git &> /dev/null; then
   sudo apt -y install git
fi
#
# clone the repository to a local user directory and execute install script
git clone -b "master" https://github.com/gregory-whaley/sound_of_speed.git ${HOME}/sos_master

$HOME/sos_master/config/install.sh
#
if [ ${PIPESTATUS[0]} -eq 0 ];then
  echo "Installation completed successfully"
  sudo reboot
else
  echo "The installation exited unsuccessfully."
  exit 1
fi
