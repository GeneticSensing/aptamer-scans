#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Each chip has 4 working electrodes with the same solution.
There are 16 chips. A cycle is scanning all 16 chips, for a total of 64 working electrodes.
For every 12 cycles, a calibration scan for each chip is performed 
in addition to partial SWV scans to determine baseline and peak values.
After a maximum of 336 cycles, the experiment is completed.

This script should be run and monitored in a terminal.
Errors are caught and logged, but will not terminate the experiment unless connection between
the RPi and Emstat is lost.

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

### Types ###

Curve = list[list[palmsens.mscript.MScriptVar]]

### Constants ###

LOG = logging.getLogger(__name__)
DEVICE_PORT = None # (None = auto detect).
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
# Measurement
WE_PER_CHIP = 4
NUM_CHIPS = 16
N = 12 # Number of cycles between calibration cycle
MAX_CYCLES = 336
# Teensy
WE_CHANGE_ACK_PIN    = 25  # Pin 22 to send signal to Teensy
CH_CHANGE_ACK_PIN    = 8   # Pin 24 to receive signal from Teensy
CYCLE_CHANGE_ACK_PIN = 7   # Pin 26 to receive signal from Teensy
CH_CHANGE_PIN        = 11  # Pin 23 to send signal to Teensy

### Globals ###
chip = gpiod.Chip('gpiochip4')
ch_change_line = chip.get_line(CH_CHANGE_PIN)
output_lines = chip.get_lines([CH_CHANGE_ACK_PIN, CYCLE_CHANGE_ACK_PIN])
elctrd_cntr = 0
cycle_start_time = time.time()
baseline_peak_values: list[tuple[float, float]] = [(0, 0)] * NUM_CHIPS

### Methods ###

def setup():
  # Logging
  logging.basicConfig(level=logging.DEBUG, format='[%(module)s] %(message)s', stream=sys.stdout)
  logging.getLogger('matplotlib').setLevel(logging.INFO)
  logging.getLogger('PIL.PngImagePlugin').setLevel(logging.INFO)
  # Pin config
  ch_change_line.request(consumer="RPi-Teensy", type=gpiod.LINE_REQ_DIR_OUT)
  output_lines.request(consumer="RPi-Teensy", type=gpiod.LINE_REQ_EV_BOTH_EDGES)

def write_curve_to_csv(file: typing.IO, curve: Curve):
  file.write('sep=;\n')
  writer = csv.writer(file, delimiter=';')
  # Write header row.
  writer.writerow([f'{value.type.name} [{value.type.unit}]' for value in curve[0]])
  # Write data rows.
  for package in curve:
    writer.writerow([value.value for value in package])

def get_scanning_windows() -> dict[str, str]:
  chip_index = ((elctrd_cntr * WE_PER_CHIP) // NUM_CHIPS) % NUM_CHIPS
  peak, left_baseline = baseline_peak_values[chip_index] 
  return {
    "<E_begin_baseline>": f"{int(left_baseline*1000) - 30}m",
    "<E_end_baseline>": f"{int(left_baseline*1000)}m",
    "<E_begin_peak>": f"{int(peak*1000) - 15}m",
    "<E_end_peak>": f"{int(peak*1000) + 15}m"
  }

def update_method_script(template_path: str, dest_path: str, replacements: dict):
  with open(template_path, "r") as f:
    content = f.read()
  for placeholder, value in replacements.items():
    content = content.replace(placeholder, value)
  with open(dest_path, "w", newline='\n') as f:
    f.write(content)

def update_baseline_peak_values(potentials: np.ndarray, currents: np.ndarray) -> np.ndarray:
  # Filter data using butterworth to prevent noise affecting peak detection
  currents_butter = butterworth_filter(currents)
  # Get all samples where -0.4 mV <= applied potential >= -0.05 mV (removes cathode spike)
  start, end = np.searchsorted(potentials, [-0.4, -0.05])
  trunc_x = potentials[start:end]
  trunc_y = currents_butter[start:end]
  peak, baseline = find_peak_and_baseline(trunc_x, trunc_y)
  chip_index = ((elctrd_cntr * WE_PER_CHIP) // NUM_CHIPS) % NUM_CHIPS
  baseline_peak_values[chip_index] = (peak, baseline)
  return currents_butter

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

def find_peak_and_baseline(potentials: np.ndarray, currents: np.ndarray) -> tuple[float, float]:
  # Parameters
  prominence_threshold = 5e-7
  distance_threshold = 100
  # TODO: Apply baseline correction
  peaks, properties = sg.find_peaks(-currents, prominence=prominence_threshold, distance=distance_threshold)
  if len(peaks) == 0:
    print("No peak found! Please recalibrate.")
    return 0, 0 # TODO: Use next WE to find peak
  if len(peaks) > 1:
    print("More than one peak found!")
    # Return peak with the max current
    i_max_peak = min(range(len(peaks)), key=lambda i: currents[peaks[i]])
    return potentials[peaks[i_max_peak]], potentials[properties['left_bases'][i_max_peak]]
  return potentials[peaks[0]], potentials[properties['left_bases'][0]]

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

def perform_calibration_scan(device: Instrument) -> Curve:
  calibration_scan = exec_scan(CALIBRATION_SWV_PATH, device)
  # Update baseline and peak values
  xvalues = palmsens.mscript.get_values_by_column([calibration_scan], 0)
  yvalues = palmsens.mscript.get_values_by_column([calibration_scan], 1)
  update_baseline_peak_values(xvalues, yvalues)
  
  base_name = f"{elctrd_cntr}_FULL_100Hz_{get_formatted_date()}"
  base_path = os.path.join(OUTPUT_PATH, base_name)
  with open(base_path + '.csv', 'wt', newline='') as f:
    write_curve_to_csv(f, calibration_scan)
  return calibration_scan

def perform_partial_scans(device: Instrument) -> Curve:
  partial_scans: Curve = []
  for scan in PARTIAL_SWV_SCANS:
    replacements = get_scanning_windows()
    template_path = f"{PARTIAL_SWV_PATH_PREFIX}{scan}_template.mscr"
    script_path = f"{PARTIAL_SWV_PATH_PREFIX}{scan}.mscr"
    update_method_script(template_path, script_path, replacements)
    partial_scan = exec_scan(script_path, device)
    partial_scan[0][1].type.name += f" {scan}"
    if not partial_scans:
      partial_scans = partial_scan
    else:
      partial_scans = concat_partial_scans(partial_scans, partial_scan)

  base_name = f"{elctrd_cntr}_PARTIAL_5-100Hz_{get_formatted_date()}"
  base_path = os.path.join(OUTPUT_PATH, base_name)
  with open(base_path + '.csv', 'wt', newline='') as f:
    write_curve_to_csv(f, partial_scans)
  return partial_scans

def concat_partial_scans(previous_scans: Curve, new_scan: Curve) -> Curve:
  a = np.asarray(previous_scans)
  b = np.asarray(new_scan)[:, 1:] # Exclude the redundant potential column
  return np.concatenate((a, b), axis=1).tolist()

def perform_scan():
  is_calibration = elctrd_cntr % WE_PER_CHIP == 0 and (elctrd_cntr // (NUM_CHIPS * WE_PER_CHIP)) % N == 0
  LOG.info(f"Starting partial SWV scan {'including calibration scan' if is_calibration else ''}.")
  directory_name = f"{elctrd_cntr}_{get_formatted_date()}"
  base_dir = os.path.join(OUTPUT_PATH, directory_name)
  os.makedirs(base_dir, exist_ok=True)

  port = DEVICE_PORT
  if port is None:
    port = palmsens.serial.auto_detect_port()

  # Create and open serial connection to the device.
  with palmsens.serial.Serial(port, 1) as comm:
    device = Instrument(comm)
    device_type = device.get_device_type()
    if device_type != palmsens.instrument.DeviceType.EMSTAT_PICO and 'EmStat4' not in device_type:
      comm.close()
      raise RuntimeError("Device is not an Emstat Pico or EmStat4")
    LOG.info('Connected to %s.', device_type)

    calibration_scan = perform_calibration_scan(device) if is_calibration else None
    partial_scans = perform_partial_scans(device)

  if calibration_scan:
    plot_curve(calibration_scan, is_calibration)
  plot_curve(partial_scans)

  elctrd_cntr += 1
  send_teensy_signal()

def plot_curve(curve: Curve, is_calibration: bool = False):
  plt.figure()
  plt.title(base_path)
  # Configure the X and Y axis labels
  xvar = curve[0][0]
  plt.xlabel(f'{xvar.type.name} [{xvar.type.unit}]')
  yvar = curve[0][1]
  plt.ylabel(f'{yvar.type.name} [{yvar.type.unit}]')
  # Configure grid
  plt.grid(visible=True, which='major', linestyle='-')
  plt.grid(visible=True, which='minor', linestyle='--', alpha=0.2)
  plt.minorticks_on()
  # Loop through all scans
  xvalues = palmsens.mscript.get_values_by_column([curve], 0)
  for y_axis in range(1, len(curve[0])):
    yvalues = palmsens.mscript.get_values_by_column([curve], y_axis)
    label = curve[0][y_axis].type.name
    plt.plot(xvalues, yvalues, label=label)
  # Display the legend and save the plot
  plt.legend()
  base_name = f"{elctrd_cntr}_{'PARTIAL_5-100Hz' if is_calibration else 'FULL_100Hz'}_{get_formatted_date()}"
  base_path = os.path.join(OUTPUT_PATH, base_name)
  plt.savefig(base_path + '.png')
  plt.close()

def send_teensy_signal():
  # Send short pulse as acknowledgement signal to Teensy
  print("Raspberry Pi: Function completed. Sending acknowledgment to Teensy.")
  ch_change_line.set_value(1)
  time.sleep(1)
  ch_change_line.set_value(0)

def teensy_we_change_acknowledged():
  print("Raspberry Pi: Received acknowledgment from Teensy that WE has been changed.")
  perform_scan()

def teensy_ch_change_acknowledged():
  print("Raspberry Pi: Received acknowledgment from Teensy that chip has been changed.")
  perform_scan()

def teensy_cycle_acknowledged():
  print("Raspberry Pi: Received cycle acknowledgment from Teensy. Exiting after final measurement.")
  if elctrd_cntr >= MAX_CYCLES * WE_PER_CHIP * NUM_CHIPS:
    print("Maximum number of cycles reached. Exiting.")
    sys.exit(0)
  timer_wait(30)
  perform_scan()

def timer_wait(num_minutes: int):
  while True:
    now = time.time()
    if now - cycle_start_time >= num_minutes * 60:
      cycle_start_time = now
      return
    time.sleep(60)

def main():
  try:
    setup()
    perform_scan()
    while True:
      # Wait for an edge event (blocking wait with timeout of 10 seconds)
      if output_lines.event_wait():
        # Process the edge event
        events = output_lines.event_read()
        for event in events:
          if event.type != gpiod.LineEvent.RISING_EDGE:
            continue
          actions = {
            WE_CHANGE_ACK_PIN: teensy_we_change_acknowledged,
            CH_CHANGE_ACK_PIN: teensy_ch_change_acknowledged,
            CYCLE_CHANGE_ACK_PIN: teensy_cycle_acknowledged
          }
          if action := actions.get(event.offset):
            action()
      # Keep the program running indefinitely
      time.sleep(1)
  finally:
    ch_change_line.release()
    output_lines.release()
