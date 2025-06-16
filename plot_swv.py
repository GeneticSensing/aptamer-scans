#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script runs one scan at a time.

:author: Adam Mak <adam-mak>, Sadman Sakib <ssadman70>

-------------------------------------------------------------------------------
Copyright (c) 2019-2021 PalmSens BV
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

   - Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
   - Neither the name of PalmSens BV nor the names of its contributors
     may be used to endorse or promote products derived from this software
     without specific prior written permission.
   - This license does not release you from any requirement to obtain separate
     licenses from 3rd party patent holders to use this software.
   - Use of the software either in source or binary form must be connected to,
     run on or loaded to an PalmSens BV component.

DISCLAIMER: THIS SOFTWARE IS PROVIDED BY PALMSENS "AS IS" AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

### Imports ###

# Standard library
import argparse
import csv
import datetime
import json
import logging
import os
import os.path
import sys
import time
import typing
# Third-party
import gpiod # unavailable on non-linux systems, and must be installed globally
import matplotlib.pyplot as plt
import numpy as np
import scipy.signal as sg
# Local
import palmsens.instrument
import palmsens.mscript
import palmsens.serial
from palmsens.instrument import Instrument
from pstrace_processing import swv_peak_finder

### Types ###

Curve = list[list[palmsens.mscript.MScriptVar]]

### Constants ###

PORT = '/dev/ttyUSB0'  # Hardcoded Serial Port
LOG = logging.getLogger(__name__)
# Paths
CALIBRATION_SWV_PATH = 'methodscripts/swv_calibration.mscr'
PARTIAL_SWV_PATH_PREFIX = 'methodscripts/partial_swv_'
PARTIAL_SWV_SCANS = [
  'baseline_5hz',
  'baseline_100hz',
  'peak_5hz',
  'peak_100hz'
]
OUTPUT_PATH = 'output'

### Globals ###
chip = gpiod.Chip('gpiochip4')
cycle_start_time = time.time()

def positive_int(val: str) -> int:
  ivalue = int(val)
  if ivalue <= 0:
    raise argparse.ArgumentTypeError(f"{val} is not a positive integer")
  return ivalue

def setup():
  # Logging
  logging.basicConfig(level=logging.DEBUG, format='[%(module)s] %(message)s', stream=sys.stdout)
  logging.getLogger('matplotlib').setLevel(logging.INFO)
  logging.getLogger('PIL.PngImagePlugin').setLevel(logging.INFO)
  # Arg parse
  parser = argparse.ArgumentParser(description="Process an electrode counter argument.")
  parser.add_argument("value", type=positive_int)
  args = parser.parse_args()
  global elctrd_cntr
  elctrd_cntr = args.value
  # Output dir
  directory_name = f"{elctrd_cntr}_{get_formatted_date()}"
  global base_dir
  base_dir = os.path.join(OUTPUT_PATH, directory_name)
  os.makedirs(base_dir, exist_ok=True)

def write_curve_to_csv(file: typing.IO, curve: Curve):
  writer = csv.writer(file, delimiter=';')
  # Write header row.
  writer.writerow([f'{value.type.name} [{value.type.unit}]' for value in curve[0]])
  # Write data rows.
  for package in curve:
    writer.writerow([value.value for value in package])

def get_replacements(peak: float, left_baseline: float) -> dict[str, str]:
  return {
    "<E_begin_baseline>": f"{int(left_baseline*1000)}m",
    "<E_end_baseline>": f"{int(left_baseline*1000) + 30}m", #not sure if this is right tho
    "<E_begin_peak>": f"{int(peak*1000) + 15}m",
    "<E_end_peak>": f"{int(peak*1000) - 15}m"
  }

def update_method_script(template_path: str, dest_path: str, replacements: dict):
  with open(template_path, "r") as f:
    content = f.read()
  for placeholder, value in replacements.items():
    content = content.replace(placeholder, value)
  with open(dest_path, "w", newline='\n') as f:
    f.write(content)

def butterworth_filter(signal: np.ndarray) -> np.ndarray:
  # Parameters
  sampling_rate    = 100 # Hz
  cutoff_frequency = 2   # Hz
  order            = 3

  # Apply the filter
  nyquist = sampling_rate / 2
  normal_cutoff = cutoff_frequency / nyquist
  b, a = sg.butter(order, normal_cutoff)
  filtered_signal = sg.filtfilt(b, a, signal)
  return filtered_signal

def find_partial_peak(potentials, currents):
  potentials = potentials[3:]
  average = sum(potentials) / len(potentials)
  
def find_peak_and_baseline(potentials: np.ndarray, currents: np.ndarray) -> tuple[float, float]:
  start, end = np.searchsorted(potentials, [-0.4, -0.05])
  trunc_x = potentials[start:end]
  trunc_y = currents[start:end]
  print(trunc_x, trunc_y)
  return swv_peak_finder.detect_peaks(trunc_x, trunc_y, 1)
  # Parameters
  prominence_threshold = 5e-7
  distance_threshold = 100

  # Filter data using butterworth to prevent noise affecting peak detection
  currents_butter = butterworth_filter(currents)
  # Get all samples where -0.4 mV <= applied potential >= -0.05 mV (removes cathode spike)
  start, end = np.searchsorted(potentials, [-0.4, -0.05])
  trunc_x = potentials[start:end]
  trunc_y = currents_butter[start:end]
 
  # TODO: Apply baseline correction
  peaks, properties = sg.find_peaks(-trunc_y, prominence=prominence_threshold, distance=distance_threshold)
  if len(peaks) == 0:
    LOG.warning("No peak found! Please recalibrate.")
    return 0, 0 # TODO: Use next WE to find peak
  if len(peaks) > 1:
    LOG.info("More than one peak found!")
    # Return peak with the max current
    i_max_peak = min(range(len(peaks)), key=lambda i: trunc_y[peaks[i]])
    return trunc_x[peaks[i_max_peak]], trunc_x[properties['left_bases'][i_max_peak]]
  return trunc_x[peaks[0]], trunc_x[properties['left_bases'][0]]

def get_formatted_date() -> str:
  now = datetime.datetime.now()
  return f"{now.strftime('%b')}_{now.day}"


def exec_scan(script_path: str, device: Instrument) -> Curve:
  # Read and send the MethodSCRIPT file.
  LOG.info('Sending MethodSCRIPT.')
  device.send_script(script_path)

  # Read the result lines.
  LOG.info('Waiting for results.')
  result_lines = device.readlines_until_end()

  # Parse the result.
  return palmsens.mscript.parse_result_lines(result_lines)[0]

def perform_calibration_scan(device: Instrument) -> tuple[Curve, float, float]:
  calibration_scan = exec_scan(CALIBRATION_SWV_PATH, device)
  # Update baseline and peak values
  xvalues = palmsens.mscript.get_values_by_column([calibration_scan], 0)
  yvalues = palmsens.mscript.get_values_by_column([calibration_scan], 1)
  peak, baseline, pkval, blval = find_peak_and_baseline(xvalues, yvalues)
  print('peak and baseline: ', peak, baseline)
  base_name = f"{elctrd_cntr}_FULL_100Hz_{get_formatted_date()}"
  base_path = os.path.join(base_dir, base_name)
  with open(base_path + '.csv', 'wt', newline='') as f:
    write_curve_to_csv(f, calibration_scan)
  return [xvalues, yvalues], pkval, blval

def perform_partial_scans(peak: float, baseline: float, device: Instrument) -> Curve:
    
  partial_scans: Curve = []
  for scan in PARTIAL_SWV_SCANS:
    replacements = get_replacements(peak, baseline)
    template_path = f"{PARTIAL_SWV_PATH_PREFIX}{scan}_template.mscr"
    script_path = f"{PARTIAL_SWV_PATH_PREFIX}{scan}.mscr"
    update_method_script(template_path, script_path, replacements)
    partial_scan = exec_scan(script_path, device)
    # partial_scan[0][1].type.name += f" {scan}"
    if not partial_scans:
      partial_scans = partial_scan
    else:
      partial_scans = concat_partial_scans(partial_scans, partial_scan)
  xvalues = palmsens.mscript.get_values_by_column([partial_scans], 0)
  yvalues = palmsens.mscript.get_values_by_column([partial_scans], 1)
  print(yvalues, '<- PARTIAL SCAN X AND Y VALUES')
  #peak, baseline, pkval, blval = find_partial_peak(xvalues, yvalues)
  
  base_name = f"{elctrd_cntr}_PARTIAL_5-100Hz_{get_formatted_date()}"
  base_path = os.path.join(base_dir, base_name)
  with open(base_path + '.csv', 'wt', newline='') as f:
    write_curve_to_csv(f, partial_scans)
  return [xvalues, yvalues]

def concat_partial_scans(previous_scans: Curve, new_scan: Curve) -> Curve:
  a = np.asarray(previous_scans)
  b = np.asarray(new_scan)
  return np.concatenate((a, b), axis=1).tolist()

def prep_for_scan(): # just connects to palmsens without running any scans, for execution in other files. 
  LOG.info(f"Starting partial SWV scan including calibration scan.")
  port = PORT #palmsens.serial.auto_detect_port()
  # Create and open serial connection to the device.
  with palmsens.serial.Serial(port, 5, baudrate=230400) as comm:
    device = Instrument(comm)
    device_type = device.get_device_type()
    if device_type != palmsens.instrument.DeviceType.EMSTAT_PICO and 'EmStat4' not in device_type:
      comm.close()
      raise RuntimeError("Device is not an Emstat Pico or EmStat4")
    LOG.info('Connected to %s.', device_type)
  #return device

def full_scan():
  LOG.info(f"Starting partial SWV scan including calibration scan.")
  port = PORT #palmsens.serial.auto_detect_port()
  # Create and open serial connection to the device.
  with palmsens.serial.Serial(port, 5, baudrate=230400) as comm:
    device = Instrument(comm)
    device_type = device.get_device_type()
    if device_type != palmsens.instrument.DeviceType.EMSTAT_PICO and 'EmStat4' not in device_type:
      comm.close()
      raise RuntimeError("Device is not an Emstat Pico or EmStat4")
    LOG.info('Connected to %s.', device_type)

    calibration_scan, peak, baseline = perform_calibration_scan(device)
    return [calibration_scan, peak, baseline]

def partial_scan(peak, baseline):
  LOG.info(f"Starting partial SWV scan including calibration scan.")
  port = PORT #palmsens.serial.auto_detect_port()
  # Create and open serial connection to the device.
  with palmsens.serial.Serial(port, 5, 230400) as comm:
    device = Instrument(comm)
    device_type = device.get_device_type()
    if device_type != palmsens.instrument.DeviceType.EMSTAT_PICO and 'EmStat4' not in device_type:
      comm.close()
      raise RuntimeError("Device is not an Emstat Pico or EmStat4")
    LOG.info('Connected to %s.', device_type)

    partials = perform_partial_scans(peak, baseline, device)
    return partials
  
def plot_curve(partial_scans: Curve, calibration_scan: Curve):
  plt.figure()
  plt.title(base_dir.replace(OUTPUT_PATH, ""))
  # Configure the X and Y axis labels
  xvar = calibration_scan[0][0]
  plt.xlabel(f'{xvar.type.name} [{xvar.type.unit}]')
  yvar = calibration_scan[0][1]
  plt.ylabel(f'{yvar.type.name} [{yvar.type.unit}]')
  # Configure grid
  plt.grid(visible=True, which='major', linestyle='-')
  plt.grid(visible=True, which='minor', linestyle='--', alpha=0.2)
  plt.minorticks_on()
  # First plot the calibration scan
  xvalues = palmsens.mscript.get_values_by_column([calibration_scan], 0)
  yvalues = palmsens.mscript.get_values_by_column([calibration_scan], 1)
  plt.plot(xvalues, yvalues, label='Calibration Scan 100Hz', color='black')
  # Loop through all partial scans
  for i in range(0, len(partial_scans[0]), 2):
    xvalues = palmsens.mscript.get_values_by_column([partial_scans], i)
    yvalues = palmsens.mscript.get_values_by_column([partial_scans], i+1)
    label = partial_scans[0][i+1].type.name
    plt.plot(xvalues, yvalues, label=label)
  # Display the legend and save the plot
  plt.legend()
  base_name = f"{elctrd_cntr}_5-100Hz_{get_formatted_date()}"
  base_path = os.path.join(base_dir, base_name)
  plt.savefig(base_path + '.png')
  plt.show()

def main():
  setup()
  perform_scan()

if __name__ == '__main__':
  main()
