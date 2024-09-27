# Chronoamperometry-Aptamer

This repository contains the code and data for the Chronoamperometry-Aptamer project.

## Finding and Plotting CA Lifetimes

Export the spreadsheet from PSTrace into the `/sheets` directory. In `foo.py`, change the spreadsheet name exported from PSTrace and run it. Once successfully run, the resulting findings should be placed in `/csv` as well as a `summary.csv` to show $A$ and $\tau$ for each concentration. The findings are also plotted and curve fitted with `lmfit`'s minimizer. These can be found under `/figs`.

## Running SWV and CA Measurements on Emstat Pico

### On a Windows computer:

```shell
cd methodscripts
pip3 install -r requirements.txt
python3 -m plot_advanced_swv # SWV measurement
python3 -m plot_ca # CA measurement
```

Resulting plots are saved under `/methodscripts/output`.  

### On a Raspberry Pi:

```shell
cd methodscripts
python3 -m venv my-venv # my-venv can be any arbitrary name
source my-venv/bin/activate
pip3 install -r requirements.txt
python3 -m plot_advanced_swv # SWV measurement
python3 -m plot_ca # CA measurement
```

Here's a [document](https://mcmasteru365-my.sharepoint.com/:w:/g/personal/maka9_mcmaster_ca/Efdt9OWZqZZOsVK4q_6w3oYBpbUoHyyxUG8_DpgKnCxJOw?e=ourUAt) for further explanation.  

_Note_: Emstat Pico's cannot be recognized as a MethodSCRIPT device under MacOS.