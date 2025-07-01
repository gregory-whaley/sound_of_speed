#!/usr/bin/env bash
#  install script for the Speed of Sound system.
#  G. Whaley.  
#  26 Jun 25
#
set -x          # Debugging
set -e          # exit installation if anything fails
exec > >(tee -i installation-$(date +%F).txt) 2>&1          # Make log file

BASE_DIR=$HOME/sos_master
export BASE_DIR=$BASE_DIR

cd $BASE_DIR || exit 1

# install support applications
#
# first configure the firewall ports for access outside this server
if  ! which ufw &> /dev/null; then
   sudo apt install -y ufw       # firewall config utility
fi
sudo ufw allow 22,80,443,1883,8888,8889/tcp
#  22=ssh, 80 and 443 = web, 1883 = MQTT, 8888 & 8889 = websockets
sudo ufw --force enable


# install pip3:
if  ! which pip3 &> /dev/null; then
   sudo apt install python3-pip
fi

#Install mosquitto server:
if  ! which mosquitto &> /dev/null; then
   sudo apt install -y mosquitto
fi
# add mosquitto config file for serving MQTT port 1883 and Websocket port 8889
#sudo cp $BASE_DIR/config/sos_mosquitto.config /etc/mosquitto/conf.d/
#sudo systemctl restart mosquitto.service

# install apache web server
#if  ! which apache2 &> /dev/null; then
#   sudo apt install -y apache2
#fi

# install portaudio library needed by sounddevice python module
if dpkg --status portaudio19-dev &>/dev/null; then
   echo "portaudio19-dev is installed."
else
   echo "portaudio19-dev is not installed."
   sudo apt install -y portaudio19-dev
fi

# create python virtual environment
cd $BASE_DIR || exit 1
if ! [ -d .sos_venv ]; then
   python3 -m venv .sos_venv       # generate venv; the dot keeps the subfolder hidden
fi
source ./.sos_venv/bin/activate

# install needed python modules
pip3 install -U -r $BASE_DIR/config/requirements.txt   #  -U upgrades the module if already present on system


# install system services:
sudo cp $BASE_DIR/config/sos_capture.service /etc/systemd/system
sudo sed -i 's^dummy_user^'$USER'^' /etc/systemd/system/sos_capture.service
sudo sed -i 's^dummy_directory^'$BASE_DIR'^g' /etc/systemd/system/sos_capture.service
sudo systemctl enable sos_capture.service


sudo cp $BASE_DIR/config/zmq_bridge.service /etc/systemd/system
sudo sed -i 's^dummy_user^'$USER'^' /etc/systemd/system/zmq_bridge.service
sudo sed -i 's^dummy_directory^'$BASE_DIR'^g' /etc/systemd/system/zmq_bridge.service
sudo systemctl enable zmq_bridge.service

sudo cp $BASE_DIR/config/local_http.service /etc/systemd/system
sudo sed -i 's^dummy_directory^'$BASE_DIR'^g' /etc/systemd/system/local_http.service
sudo systemctl enable local_http.service

cp -p $BASE_DIR/config/generate_plots_template.sh $BASE_DIR/sos_capture/generate_plots.sh
sed -i 's^dummy_directory^'$BASE_DIR'^g' $BASE_DIR/sos_capture/generate_plots.sh
cp $BASE_DIR/config/no_data.png $BASE_DIR/sos_capture/daily_scatterplot.png
cp $BASE_DIR/config/no_data.png $BASE_DIR/sos_capture/totals_by_day.png
cp $BASE_DIR/config/no_data.png $BASE_DIR/sos_capture/histograms_by_day.png


sudo cp $BASE_DIR/config/sos_cron /etc/cron.d/
sudo sed -i "s^dummy_user^"$USER"^g" /etc/cron.d/sos_cron
sudo sed -i "s^dummy_directory^"$BASE_DIR"^g" /etc/cron.d/sos_cron


exit 0     # no errors if we made it this far

