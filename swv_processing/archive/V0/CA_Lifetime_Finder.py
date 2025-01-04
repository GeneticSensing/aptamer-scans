# -*- coding: utf-8 -*-
"""
Created on Wed Aug 14 19:44:09 2024

@author: ssadm
"""

import csv
import numpy as np
from lmfit import minimize, Parameters, report_fit
import matplotlib.pyplot as plt

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

# Perform curve fitting using lmfit minimize
def perform_curve_fitting(xdata, ydata):
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
    plt.show()

    return result

# Main function for standalone execution
def main():
    # Ask the user to enter the CSV file name
    file_name = "Glcucose - 1.5 mM A.csv"
    xdata, ydata = read_csv(file_name)
    perform_curve_fitting(xdata, ydata)

# Allow the script to be both callable as a library and runnable as a standalone program
if __name__ == '__main__':
    main()
