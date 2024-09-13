# Description: This script is used to run the PSTraceSeparation and CA_Lifetime_Finder scripts together.
"""
Created on Fri Sep 6 17:40 2024

@author: adam-mak
"""

import csv
import os

from PSTraceSeparation import pstracetoinput
from CA_Lifetime_Finder import read_df, perform_curve_fitting

# Pre-fill this variable with the spreadsheet path and name
SPREADSHEET_NAME = 'CA Probe Optimization Experiment - Blanks.xlsx'

def save_summary_csv(summary):
    summary_csv_path = os.path.abspath(os.path.join('..', 'csv', 'summary.csv'))
    with open(summary_csv_path, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(['Sample Name', 'A', 'tau'])
        for row in summary:
            writer.writerow([row['filename'], row['params']['A'].value, row['params']['tau'].value])

def main():
    if os.getcwd() != os.path.dirname(os.path.abspath(__file__)):
        if not os.getcwd().endswith('Chronoamperometry-Aptasensor'):
            raise Exception("Please run this script from the same directory as the script or project directory.")
        os.chdir('scripts')

    dfs = pstracetoinput(SPREADSHEET_NAME)
    summary = []
    for df in dfs:
        xData, yData, title = read_df(df)
        params = perform_curve_fitting(xData, yData, title)
        summary.append({'params': params, 'filename': title})
    save_summary_csv(summary)

# If the script is run directly, execute the function with the predefined spreadsheet name
if __name__ == "__main__":
    main()
