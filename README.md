# Chronoamperometry-Aptamer

This repository contains the code and data for the Chronoamperometry-Aptamer project. There will be an upcoming change to use Square Wave Voltammetry (SWV) instead of Chronoamperometry (CA).

## Finding and Plotting SWV Measurements

Export the spreadsheet from PSTrace into the `/sheets` directory. In `swv_processing.py`, change the spreadsheet name exported from PSTrace and run it. Once successfully run, the resulting findings should be placed in `/csv` as well as a `summary.csv` to show $A$ and $\tau$ for each concentration.

## Running SWV Measurements on Emstat Pico

### On a Windows computer:

```shell
cd methodscripts
pip3 install -r requirements.txt
python3 -m plot_advanced_swv # SWV measurement
python3 -m plot_advanced_partial_swv # Partial SWV measurement
```

Resulting plots are saved under `/methodscripts/output`.  

### On a Raspberry Pi:

```shell
cd methodscripts
python3 -m venv my-venv # my-venv can be any arbitrary name
source my-venv/bin/activate
pip3 install -r requirements.txt
python3 -m plot_advanced_swv # SWV measurement
python3 -m plot_advanced_partial_swv # Partial SWV measurement
```

Here's a [document](https://mcmasteru365-my.sharepoint.com/:w:/g/personal/maka9_mcmaster_ca/Efdt9OWZqZZOsVK4q_6w3oYBpbUoHyyxUG8_DpgKnCxJOw?e=ourUAt) to use PalmSens MethodSCRIPT Examples repo.

_Note_: Emstat Pico's cannot be recognized as a MethodSCRIPT device under MacOS.
