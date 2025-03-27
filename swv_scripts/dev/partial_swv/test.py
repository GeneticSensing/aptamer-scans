import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from io import StringIO
from scipy.signal import butter, filtfilt

# CSV path
SWV_CSV_PATH = 'full_5mM.csv'
PARTIAL_SWV_CSV_PATH = 'partial_5mM.csv'

"""
Converts measurement to a dataframe

i_meas is the measurement index (0 is first measurement taken, 1 is second, so on...)
"""
def convert_csv_to_df(path: str, i_meas: int) -> pd.DataFrame:
  # Load the CSV file
  with open(path, 'r') as file:
    # Read the content to identify the duplicate header rows
    lines = file.readlines()

  # Define the header string to locate
  header = lines[1]

  # Start processing from the last (second) header occurrence
  header_lines = [i for i, line in enumerate(lines) if line == header]
  start_line = header_lines[i_meas]
  if len(header_lines) > i_meas + 1:
    end_line = header_lines[i_meas+1]
    data = lines[start_line:end_line]
  else:
    data = lines[start_line:]
  
  # Convert the subset of lines into a DataFrame directly in-memory
  data_string = "".join(data)
  df = pd.read_csv(StringIO(data_string), delimiter=';')
  
  return df


def filter(signal: np.ndarray, cutoff_frequency: float) -> np.ndarray:
  # Parameters
  sampling_rate = 100  # Hz
  order = 2

  # Apply the filter
  nyquist = sampling_rate / 2
  normal_cutoff = cutoff_frequency / nyquist
  b, a = butter(order, normal_cutoff)
  filtered_signal = filtfilt(b, a, signal)
  return filtered_signal


def display(dfs: list[pd.DataFrame], names: list[str]):
  CATHODE_SPIKE_OFFSET = 2
  plt.figure()
  for i in range(len(dfs)):
    potentials = dfs[i].iloc[CATHODE_SPIKE_OFFSET:, 0]
    currents = dfs[i].iloc[CATHODE_SPIKE_OFFSET:, 1]
    plt.plot(potentials, currents, label=names[i])
  plt.xlabel('Applied Potential [V]')
  plt.ylabel('Current [A]')
  plt.title('Full and Partial SWV with EmStat4')
  plt.legend()
  plt.grid(True)
  plt.show()

def main():
  dfs = []
  names = []

  dfs.append(convert_csv_to_df(SWV_CSV_PATH, 0))
  names.append("Cell Off")
  dfs.append(convert_csv_to_df(SWV_CSV_PATH, 1))
  names.append("Cell On")
  dfs.append(convert_csv_to_df(PARTIAL_SWV_CSV_PATH, 0))
  names.append("Cell Off (baseline)")
  dfs.append(convert_csv_to_df(PARTIAL_SWV_CSV_PATH, 1))
  names.append("Cell On (baseline)")
  dfs.append(convert_csv_to_df(PARTIAL_SWV_CSV_PATH, 2))
  names.append("Cell Off (peak)")
  dfs.append(convert_csv_to_df(PARTIAL_SWV_CSV_PATH, 3))
  names.append("Cell On (peak)")

  # Plot signals
  display(dfs, names)


if __name__ == '__main__':
  main()
