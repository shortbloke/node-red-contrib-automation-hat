# Node-RED nodes for Pimoroni Automation HAT/pHAT

## Provides nodes:
* Automation HAT:
  * Output Node: Sinking Outputs, Relays, Lights
  * Input Node: Buffered 5V Inputs (binary), 12-bit ADC @ 0-24V (±2% accuracy) Inputs (ADC1-3 only)

#### Unsupported features:
* ADC4: 12-bit ADC @ 0-3.3V
* Other Pins exposed only break out section: SPI, TX (#14), RX (#15), #25 pins 
* Controlling individual indicator lights on each input/output beyond the auto_lights capability.

## Installation
### Dependency - Node and Node-Red
Details of how to install Node and Node-Red needed for this project on Raspberry Pi can be found [here](https://nodered.org/docs/hardware/raspberrypi). The script at the top of the page ensures you have the latest supported versions ready for this project.

### Dependency - Automation HAT Python Library
First you'll need the Python dependencies for Automation HAT, you can install these with our one-line installer (as per instructions at: https://github.com/pimoroni/automation-hat):
```
curl https://get.pimoroni.com/automationhat | bash
```

### Automation HAT Node-RED
#### Installation via NPM
```
npm install node-red-contrib-automation-hat
```
#### Installation from latest source on GitHub
To install this node you should:
* Change to your users node-red nodes directory:
    ```
    cd ~/.node-red/node_modules
    ```
    _Note: older node installation may use the location: `~/.node-red/nodes`):_
* Clone this repository:
    ```
    git clone https://github.com/shortbloke/node-red-contrib-automation-hat
    ```
* Start Node-Red and you should see the new Automation HAT nodes within the Raspberry Pi section.

## To Do
In no particular order:
* Consider spliting input and outputs types into separate node files
* Add example Node-Red flows
* Add documentation
* Document specific characteristics/limitations of pHAT vs HAT
* Add support for controlling light brightness via `write` command
* Add support for controlling each individual indicator light for each input and output

## References
This project is based on the ExplorerHAT node implementation published by Pimoroni: https://github.com/pimoroni/node-red-nodes