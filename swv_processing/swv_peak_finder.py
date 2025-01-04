#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Wed Aug 14 19:44:09 2024
Last Revised on Sat Sep 14 13:04:09 2024

@author: ssadm
"""

import csv
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.signal import find_peaks

# Pre-fill CSV file path and name for standalone execution
FILENAME = "Glucose - 1.5 mM A.csv"

# Function to model the curve I(t) = (A * exp(-t/tau)) + B
def model_function(params, t):
    A = params['A']
    tau = params['tau']
    return A * np.exp(-t/tau)

# Function to calculate the residuals (difference between model and data)
def residuals(params, t, data):
    model = model_function(params, t)
    return model - data

# Read the CSV file
def read_csv(file_name):
    xdata = []
    ydata = []
    with open(file_name, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header if it exists
        for row in reader:
            xdata.append(float(row[0]))
            ydata.append(float(row[1]))
    del xdata[0:10]
    del ydata[0:10]
    return np.array(xdata), np.array(ydata)

# Convert dataframe to numpy arrays
def read_df(df: pd.DataFrame):
    title = df.columns[0]
    xdata = df.iloc[1:, 0].astype(float).to_list()
    ydata = df.iloc[1:, 1].astype(float).to_list()
    del xdata[0:10]
    del ydata[0:10]

    return np.array(xdata), np.array(ydata), title

# Perform peak detection using scipy.signal.find_peaks
def detect_peaks(xdata, ydata, filename):
    prominence_threshold = 0.15
    peaks, properties = find_peaks(ydata, prominence=prominence_threshold, distance=100)
    result = {}

    # Plot the data and the fitted curve
    plt.figure()
    plt.scatter(xdata, ydata, label='Data')
    plt.scatter(xdata[peaks], ydata[peaks], label='Peaks', color='red', marker='x', s=100)
    plt.xlabel('Voltage (V)')
    plt.ylabel('Current (uA)')
    plt.legend()

    if len(peaks) == 0:
        print("No peaks found!")
    if len(peaks) > 1:
        print("More than one peak found!")

    # Annotate the peak with its potential, current, and magnitude
    for i, peak_idx in enumerate(peaks):
        x_peak = xdata[peak_idx]  # Potential at peak
        y_peak = ydata[peak_idx]  # Current at peak

        # Calculate the right baseline
        right_base = properties['right_bases'][i]
        y_right_baseline = ydata[right_base]

        # Calculate the left baseline
        left_base = properties['left_bases'][i]
        y_left_baseline = ydata[left_base]

        # Calculate the intersection point of the baseline line with the peak
        peak_width = xdata[right_base] - xdata[left_base]
        slope = (y_right_baseline - y_left_baseline) / peak_width
        y_intersect = y_left_baseline + slope * (x_peak - xdata[left_base])

        # Calculate the magnitude using the intersection point
        magnitude = y_peak - y_intersect

        # Draw a line between the left and right baselines
        plt.plot([xdata[left_base], xdata[right_base]], [y_left_baseline, y_right_baseline], 'k--', linewidth=1)

        # Draw a line from the peak to the intersection
        plt.plot([x_peak, x_peak], [y_peak - magnitude, y_peak], 'k--', linewidth=1)
        
        # Create the annotation string
        annotation_text = (
            f'Potential: {x_peak:.2f} V\n'
            f'Current: {y_peak:.2f} µA\n'
            f'Magnitude: {abs(magnitude):.2f} µA'
        )
        
        # Annotate at a slight offset from the peak (top right)
        plt.annotate(annotation_text, (x_peak, y_peak),
                    xytext=(10, 20), textcoords='offset points',
                    arrowprops=dict(facecolor='black', arrowstyle='->'),
                    fontsize=8)
        
        result = {'peak_voltage': x_peak, 'peak_amplitude': magnitude, 'peak_width': abs(peak_width)}

    # Save the figure to the /figs directory
    fig_path = os.path.abspath(os.path.join('figs', f'{filename}.png'))
    plt.savefig(fig_path)
    plt.close()

    return result

# Main function for standalone execution
def main():
    xdata, ydata = read_csv(FILENAME)
    detect_peaks(xdata, ydata)

# Allow the script to be both callable as a library and runnable as a standalone program
if __name__ == '__main__':
    main()
