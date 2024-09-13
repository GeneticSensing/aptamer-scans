# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 19:44:09 2024

@author: ssadm
"""

import csv
import numpy as np
from lmfit import minimize, Parameters, report_fit
import matplotlib.pyplot as plt
import os

# Pre-fill CSV file path and name for standalone execution
filename = "Glcucose - 1.5 mM A.csv"

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
def read_df(df):
    title = df.columns[0]
    xdata = df.iloc[1:, 0].astype(float).to_list()
    ydata = df.iloc[1:, 1].astype(float).to_list()
    del xdata[0:10]
    del ydata[0:10]

    return np.array(xdata), np.array(ydata), title

# Perform curve fitting for one df using lmfit minimize - only for standalone execution
def perform_curve_fitting(xdata, ydata, filename):
    # Create a set of Parameters
    params = Parameters()
    params.add('A', value=2)
    params.add('tau', value=0.003)

    # Perform the least squares minimization
    result = minimize(residuals, params, args=(xdata, ydata))

    # Print the fitting results
    report_fit(result.params)

    # Plot the data and the fitted curve
    plt.figure()
    plt.scatter(xdata, ydata, label='Data')
    plt.plot(xdata, model_function(result.params, xdata), label='Best Fit', color='red')
    plt.xlabel('Time (s)')
    plt.ylabel('Current (uA)')
    plt.legend()

    fig_path = os.path.abspath(os.path.join('..', 'figs', f'{filename}.png'))
    plt.savefig(fig_path)
    plt.close()

    return result.params

# Main function for standalone execution
def main():
    xdata, ydata = read_csv(filename)
    perform_curve_fitting(xdata, ydata)

# Allow the script to be both callable as a library and runnable as a standalone program
if __name__ == '__main__':
    main()
