<!-- Update the logo URL to point to github -->

[<h1 align="center"> <img src="sos_dash/dist/sos_logo.png" width="200"/>](sos_dash/dist/sos_logo.png) </h1>
<h1 align="center">Speed of Sound</h1>

Automobile traffic monitor using acoustic microphones and Raspberry Pi Zero 2W, 3A or B, 4 or 5.

## Introduction
This project uses two ordinary microphones connected to a Raspberry Pi computer to measure the speed of traffic on a two lane street.  This is useful for gathering statistics of traffic speeds and volume.

### Features:
- Low cost of hardware consisting of a Raspberry Pi, two identical microphones in a all-weather enclosures facing a road, and a stereo microphone to USB converter.
- Logging of vehicle speed, direction, and time of day into a SQL database file.
- Integrated web server to display results on any local browser.

### Background
A description of the principle of operation is available [here](https://hackaday.io/project/190670-sound-of-speed).
This system is limited to a two-lane roadway with each lane traveling in opposite directions.  The tire noise made by a moving vehicle is picked up by the microphones and tracked as it passes by.  The computer calculates the speed of each vehicle and logs the time of day but does not identify the vehicle. Each steup needs to configure the horizontal spacing between the left and right microphones (30 to 100 cm) and the distance from the microphones to the roadway (5 to 50 meters).


This system uses precise measurements of time delay between microphones and so it is required that a single STEREO USB converter is used and not two separate USB microphones.

## Hardware Requirements
- Computer: Raspberry Pi Zero 2W, 3A or 3B, 4, or 5 should all work.  This code is tested using a Pi Zero 2W and operates comfortably.
- USB stereo microphone adapter.  A single, stereo adapter is required to ensure both microphones are sampled at the same time.  Additionally, for long-term use the microphones should each be placed in a weather-tolerant housing to protect the microphones from the elements.  PVC pipe or "Loc-Line" hoses work acceptably.
- Local network to view results via web browser.
- Internet access for Raspberry Pi for initial installation.

## Installing / Getting started

These installation instructions assume a freshly installed Raspian Bookworm __Lite__ installation.  The __Lite__ version of the OS is needed because there is a conflict between this audio processing code and the audio utility _pulseaudio_ and the normal and full installs of Raspian include _pulseaudio_ and _pipewire_ by default as a part of the Gnome desktop environment.

Test to ensure the OS recognizes the audio capture device with the ALSA command:
```
arecord -l
```
The computer should list all available audio input devices including the stereo microphone adapter.

Once the computer is configured with network access, open an SSH shell into the computer and execute the following install script from the user directory:

```shell
curl -s https://raw.githubusercontent.com/gregory-whaley/sound_of_speed/sos_master/config/pre_installer.sh | bash
```

The script will collect and install all the required libraries and then reboot.  The Sound of Speed system automatically starts upon booting.  The speed display is available at:
```
http://hostname.local/
```
where `hostname` is the name of the computer assigned with the OS install.  Note that `https://` is not supported at this time.  Here is a screenshot of an example measurement:
![Example Screenshot](http://)
<!-- Update the image URL to point to github -->


### Initial Configuration
The user must update and save the configuration text file using, for example, the command:

```
nano ~/sos_master/sos_capture/sos.config
```

The soundcard sampling rate must be updated in the config file to match the highest rate allowed by the hardware, either 44100 or 48000 are acceptable.  The user must measure the distance between microphones (in meters) and include that on the appropriate line.  Also the distance from the microphones to each lane of the roadway (in meters) must also be updated.  One lane of traffic will be considered a "positive" speed for either left to right or right to left motion for a given orientation of the two microphones (left and right).  Swapping the microphone positions will flip the positive speed measurement to a negative speed measurement, and vice versa.



## Contributing

If you have trouble installing or operating this system, please feel free to leave an issue entry on GitHub.  This is pre-beta software and there are likely to be bugs.


## Links

Even though this information can be found inside the project on machine-readable
format like in a .json file, it's good to include a summary of most useful
links to humans using your project. You can include links like:

- Project homepage: :https://hackaday.io/project/190670-sound-of-speed/
- Repository: https://github.com/gregory-whaley/sound_of_speed/
- Issue tracker: https://github.com/gregory-whaley/sound_of_speed/issues


## Licensing

The code in this project is licensed under MIT license.
