import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from io import StringIO
from scipy.signal import butter, filtfilt

# CSV path
SWV_CSV_PATH = 'ms_plot_swv_90hz.csv'


def convert_csv_to_df(path: str) -> pd.DataFrame:
  # Load the CSV file
  with open(path, 'r') as file:
    # Read the content to identify the duplicate header rows
    lines = file.readlines()

  # Define the header string to locate
  header = lines[1]

  # Start processing from the last (second) header occurrence
  start_line = [i for i, line in enumerate(lines) if line == header][-1]
  data_from_second_header = lines[start_line:]
  
  # Convert the subset of lines into a DataFrame directly in-memory
  data_string = "".join(data_from_second_header)
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


def display(df: pd.DataFrame):
  plt.figure()
  plt.plot(df.iloc[:, 0], df.iloc[:, 1], label='Original Signal', linestyle='--')
  for i in range(4, len(df.columns)):
    plt.plot(df.iloc[:, 0], df.iloc[:, i], label=df.columns[i])
  plt.xlabel(df.columns[0])
  plt.ylabel('Current [A]')
  plt.title('Original and Filtered Signals (90 Hz sampling rate)')
  plt.legend()
  plt.grid(True)
  plt.show()

def main():
  # Load the data
  df = convert_csv_to_df(SWV_CSV_PATH)
  signal = df.iloc[:, 1].to_numpy()

  # Filter data and add to dataframe
  df['WE current filtered [A] (3 Hz)'] = filter(signal, 3)
  df['WE current filtered [A] (2 Hz)'] = filter(signal, 2)
  df['WE current filtered [A] (1 Hz)'] = filter(signal, 1)

  # Save the filtered data
  df.to_csv('ms_plot_swv_90hz_filtered.csv', index=False)

  # Plot the original and filtered signals
  display(df)


if __name__ == '__main__':
  main()
