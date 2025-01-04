#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Created on Fri Sep 6 17:40 2024

@author: adam-mak
"""

import csv
import os

from pstrace_separation import pstracetoinput
from swv_peak_finder import read_df, detect_peaks

# Pre-fill this variable with the spreadsheet path and name
SPREADSHEET_NAME = 'TEST File Glucose Assay SWV Peaks.xlsx'
PROJECT_NAME = 'Chronoamperometry-Aptamer'

def save_summary_csv(summary):
    summary_csv_path = os.path.abspath(os.path.join('csv', 'summary.csv'))
    with open(summary_csv_path, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['Sample Name', 'Peak Voltage', 'Peak Amplitude', 'Width'])
        for row in summary:
            peak_data = row['peak_data']
            writer.writerow([
                row['filename'], 
                peak_data['peak_voltage'], 
                peak_data['peak_amplitude'], 
                peak_data['peak_width']
            ])

# Description: This script is used to run the pstrace_separation and swv_peak_finder scripts together.
def main():
    if os.getcwd() != os.path.dirname(os.path.abspath(__file__)):
        if not os.getcwd().endswith(PROJECT_NAME):
            raise Exception("Please run this script from the same directory as the script or project directory.")
        os.chdir('swv_processing')

    dfs = pstracetoinput(SPREADSHEET_NAME)
    summary = []
    for df in dfs:
        xData, yData, title = read_df(df)
        result = detect_peaks(xData, yData, title)
        summary.append({'peak_data': result, 'filename': title})
    save_summary_csv(summary)

if __name__ == "__main__":
    main()
