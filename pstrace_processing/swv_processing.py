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
SPREADSHEET_NAME = 'Lactate 1.xlsx'
PROJECT_NAME = 'Chronoamperometry-Aptamer'

def save_summary_csv(summary):
    summary_csv_path = os.path.abspath(os.path.join('pstrace_processing', 'csv', 'summary.csv'))
    with open(summary_csv_path, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['Sample Name', 'Peak Voltage', 'Peak Amplitude'])
        for row in summary:
            peak_data = row['peak_data']
            writer.writerow([
                row['filename'], 
                peak_data['peak_voltage'],
                peak_data['peak_current'] 
            ])

# Description: This script is used to run the pstrace_separation and swv_peak_finder scripts together.
def main():
    dfs = pstracetoinput(SPREADSHEET_NAME)
    summary = []
    for df in dfs:
        xData, yData, title = read_df(df)
        result = detect_peaks(xData, yData)
        #print('hello2')
        summary.append({'peak_data': result, 'filename': title})
    save_summary_csv(summary)

if __name__ == "__main__":
    main()