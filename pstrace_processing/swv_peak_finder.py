import csv
import os
from concurrent.futures import Future, ThreadPoolExecutor

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
import scipy.signal as signal

# ==== Configuration ====

PROJECT_NAME = 'Chronoamperometry-Aptamer'
FILENAME = 'Lactate 1_lin_mod_noisy.xlsx'

# Peak detection parameters
VOLTAGE_WINDOW = 0.03                  # Voltage window around peak for refined averaging. 0.01 for very noisy data, <0.001 for smooth data
GAUSSIAN_SMOOTHING_SIGMA = 40         # Smoothing level for peak detection. 35 for noisy data, 5 for smooth data.
DERIVATIVE_MULTIPLYING_FACTOR = 1     # Multiplier for smoothing when computing derivatives. 1 for noisy data, 7 for smooth data.
PEAK_INDEX_PADDING = 30               # Window to search for true max around initial peak index. 20 for noisy data, 1 for smooth data.


# ==== Utility Functions ====

def get_local_min(y, idx):
    """Finds local minimum within PEAK_INDEX_PADDING around the given index."""
    min_val = y[idx]
    for offset in range(1, PEAK_INDEX_PADDING):
        if idx + offset < len(y):
            min_val = min(min_val, y[idx + offset])
        if idx - offset >= 0:
            min_val = min(min_val, y[idx - offset])
    return min_val

def average_current_near_voltage(x, y, center_idx):
    """Averages current values within a voltage window centered around a given index."""
    if not (0 <= center_idx < len(x)):
        raise IndexError("Index out of bounds.")
    ref_voltage = x[center_idx]
    nearby_indices = np.where(np.abs(x - ref_voltage) <= VOLTAGE_WINDOW)[0]
    return np.mean(y[nearby_indices])

def estimate_baseline(x, y, peak_idx, order=1):
    """
    Estimate the baseline current using second and third derivatives.
    Chooses the minimum current near local maxima of 2nd and 3rd derivatives.
    """
    d2 = gaussian_filter1d(y, DERIVATIVE_MULTIPLYING_FACTOR * GAUSSIAN_SMOOTHING_SIGMA, order=2)
    d3 = gaussian_filter1d(y, DERIVATIVE_MULTIPLYING_FACTOR * GAUSSIAN_SMOOTHING_SIGMA, order=3)

    if not (0 < peak_idx < len(y)):
        raise ValueError("Invalid peak index.")

    peaks_d2 = signal.argrelmax(d2[:peak_idx], order=order)[0]
    peaks_d3 = signal.argrelmax(d3[:peak_idx], order=order)[0]

    if len(peaks_d2) == 0 or len(peaks_d3) == 0:
        return None

    midpoint = int((peaks_d2[-1] + peaks_d3[-1]) / 2)
    baseline_candidates = [
        get_local_min(y, peaks_d2[-1]),
        get_local_min(y, peaks_d3[-1]),
        get_local_min(y, midpoint)
    ]

    min_current = min(baseline_candidates)
    baseline_idx = np.where(y == min_current)[0][0]
    refined_baseline = average_current_near_voltage(x, y, baseline_idx)

    return baseline_idx, refined_baseline

def read_df(df: pd.DataFrame):
    """Reads voltage and current data from a pandas DataFrame and converts to numpy arrays."""
    title = df.columns[0]
    x = df.iloc[1:, 0].astype(float).to_list()[10:]  # skip header and first 10 points
    y = df.iloc[1:, 1].astype(float).to_list()[10:]
    return np.array(x), np.array(y), title

def read_csv(filename):
    """Reads voltage/current data from CSV file and removes first 10 points."""
    x, y = [], []
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        for row in reader:
            x.append(float(row[0]))
            y.append(float(row[1]))
    return np.array(x[10:]), np.array(y[10:])

# ==== Peak Detection ====

def detect_backup_peak(x, y):
    """
    Finds the most prominent peak after Gaussian smoothing,
    then refines the current by checking nearby values.
    """
    smoothed = gaussian_filter1d(y, GAUSSIAN_SMOOTHING_SIGMA)
    local_max_indices = signal.argrelmax(smoothed)[0]

    if len(local_max_indices) == 0:
        return [], 0

    max_idx = local_max_indices[np.argmax(smoothed[local_max_indices])]

    max_current = y[max_idx]
    for offset in range(1, PEAK_INDEX_PADDING):
        if max_idx + offset < len(y):
            max_current = max(max_current, y[max_idx + offset])
        if max_idx - offset >= 0:
            max_current = max(max_current, y[max_idx - offset])

    refined_idx = np.where(y == max_current)[0][0]
    refined_current = average_current_near_voltage(x, y, refined_idx)

    return [refined_idx], refined_current

def find_slope_based_baseline(smoothed, x, y, peak_idx):
    """
    Alternative baseline detection using the slope (first derivative)
    change in regions before the peak.
    """
    dy_dx = gaussian_filter1d(smoothed, GAUSSIAN_SMOOTHING_SIGMA, order=1)
    candidates = []

    for i in range(6):
        target_voltage = -0.066 * (5 - i)
        idx = np.argmin(np.abs(x - target_voltage))
        if idx < peak_idx:
            candidates.append(idx)

    slopes = [dy_dx[i + 1] - dy_dx[i] for i in range(len(candidates) - 1)]
    max_slope_idx = slopes.index(max(slopes)) + 1
    baseline_idx = candidates[max_slope_idx]

    baseline_x = (x[baseline_idx] + x[baseline_idx + 2]) / 2
    baseline_y = y[baseline_idx]

    return [baseline_x, baseline_y]

# ==== Peak Analysis and Plotting ====

def detect_peaks(x, y, val=0):
    """
    Detects the peak and estimates the baseline.
    Optionally generates and saves a plot.
    """
    #print('hello')
    peak_indices, refined_current = detect_backup_peak(x, y)

    if not peak_indices:
        #print(f"[{label}] No peaks found.")
        return {'peak_voltage': None, 'peak_current': None}

    peak_idx = peak_indices[0]
    peak_voltage = x[peak_idx]

    # Estimate baseline
    baseline_idx, baseline_current = estimate_baseline(x, y, peak_idx)
    baseline_voltage = x[baseline_idx]

    # Subtract baseline from peak
    adjusted_current = refined_current - baseline_current
    '''
    # Plot (commented out during batch runs)
    plt.figure()
    plt.scatter(x, y, label='Raw Data')
    plt.scatter(peak_voltage, refined_current, color='red', label='Peak', marker='x', s=100)
    plt.scatter(baseline_voltage, baseline_current, color='black', label='Baseline', marker='x', s=100)
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (μA)')
    plt.legend()

    # Save plot
    fig_path = os.path.abspath(os.path.join('pstrace_processing/figs', f'{label}.png'))
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)
    plt.savefig(fig_path)
    plt.close()
    '''
    if val != 0:
        return peak_idx, baseline_idx
    else:
        return {
        'peak_voltage': float(peak_voltage),
        'peak_current': float(adjusted_current)
        }

# ==== Script Entry Point ====

def main():
    x, y = read_csv(FILENAME)
    detect_peaks(x, y, os.path.splitext(os.path.basename(FILENAME))[0])

if __name__ == '__main__':
    main()
