## Setting up environment

Prerequisites: Emstat4 or Emstat Pico, electrode with solution, and Python 3 installed.

Before running a full or partial SWV measurement, the machine must have the installed Python libraries.

### On a Windows computer:

```shell
cd swv_scripts
pip3 install -r requirements.txt
```

Resulting plots are saved under `/methodscripts/output`.  

### On a Raspberry Pi:

Raspberry Pi does not allow libraries to be installed globally. It is recommended to use a virtual environment:

```shell
cd swv_scripts
python3 -m venv my-venv # my-venv can be any arbitrary name
source my-venv/bin/activate
pip3 install -r requirements.txt
python3 -m plot_advanced_swv # SWV measurement
python3 -m plot_advanced_partial_swv # Partial SWV measurement
```

To run a full SWV measr

Here's a [document](https://mcmasteru365-my.sharepoint.com/:w:/g/personal/maka9_mcmaster_ca/Efdt9OWZqZZOsVK4q_6w3oYBpbUoHyyxUG8_DpgKnCxJOw?e=ourUAt) to use PalmSens MethodSCRIPT Examples repo.

_Note_: Emstat Pico's cannot be recognized as a MethodSCRIPT device under MacOS.
_Note_: Recommended to run measurements with Emstat4. Emstat Pico was shown to have aliasing effects, that can be solved by using a second-order Butterworth filter.
_Note_: This article provides additional information on partial SWV measurements: [https://www.mdpi.com/2079-6374/12/10/782](https://www.mdpi.com/2079-6374/12/10/782).
