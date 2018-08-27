## Node-RED nodes for Pimoroni Automation HAT/pHAT

### Provided nodes:
* Automation HAT: Output, Relays, Lights

### Unsupported features:
* Analog Inputs
* Digital Inputs
* Controlling individual indicator lights on each input/output

### Installation
#### Install Node and Node-Red
Details of how to install Node and Node-Red needed for this project on Raspberry Pi can be found [here](https://nodered.org/docs/hardware/raspberrypi). The script at the top of the page ensures you have the latest supported versions ready for this project.

#### Automation HAT Python Library
First you'll need the Python dependencies for Automation HAT, you can install these with our one-line installer:

```
curl https://get.pimoroni.com/automationhat | bash
```
As per instructions at: https://github.com/pimoroni/automation-hat

#### Automation HAT Node-RED
This package is work in progress and not available directly via npm. To install this node you should 
To install, change to your users node-red nodes directory:
```
cd ~/.node-red/node_modules
```
##### Note: older node installation may use the location: `~/.node-red/nodes`):
Then clone this repository:
```
git clone https://github.com/shortbloke/node-red-contrib-automation-hat
```
Then start Node-Red and you should see the new Automation HAT nodes within the Raspberry Pi section.

### To Do
In no particular order:
* Add support for Analog and Digital Inputs - May require extending the underlying Python Library to monitor for and trigger on changes.
* Split input and outputs types into separate node files
* Add example Node-Red flows
* Add documentation
* Document specific characteristics/limitations of pHAT vs HAT
* Add support for controlling light brightness via `write` command
* Add support for controlling each individual indicator light for each input and output

## References
This project is based on the ExplorerHAT node implementation published by Pimoroni: https://github.com/pimoroni/node-red-nodes

## Tested Configuration
Different devices and versions are likely to work, these are just notes for what I have used.
* Raspberry Pi 3 Model B Rev 1.2
* Raspbian Kernel version: 4.14.34-v7+
* Node-RED: v0.18.7
* Node.js: v8.11.2
* Python3: 3.5.3
