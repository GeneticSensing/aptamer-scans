import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

def process_and_save_csv(title, titleDuplicated, read_file):
    # Process the column
    read_file.columns = titleDuplicated
    read_file = read_file[title]
    read_file = read_file.iloc[1:]
    read_file.iloc[:, 1] = read_file.iloc[:, 1] * (-1) # absolute value of currents
    read_file.loc[-1] = ["Time [s]", "Current [uA]"]
    read_file.index = read_file.index + 1
    read_file = read_file.sort_index()
    
    # Save to CSV
    csv_path = os.path.abspath(os.path.join('..', 'csv', f'{title}.csv'))
    read_file.to_csv(csv_path, index=None, header=None, encoding="utf-8")
    
    return read_file

def pstracetoinput(spreadsheet_name):
    sheet_path = os.path.abspath(os.path.join('..', 'sheets', spreadsheet_name))
    read_file = pd.read_excel(sheet_path)
    
    title = read_file.columns.tolist()

    titleCleaned = []
    titleDuplicated = []

    for t in title:
        if "Unnamed" not in t:
            titleCleaned.append(t)
            titleDuplicated.append(t)
            titleDuplicated.append(t)

    # Use a ThreadPoolExecutor to process each column in parallel
    dfs = []
    with ThreadPoolExecutor() as executor:
        # Submit tasks to the executor
        futures = []
        for title in titleCleaned:
            future = executor.submit(
                process_and_save_csv, 
                title, 
                titleDuplicated, 
                read_file.copy()
            )
            futures.append(future)

        # Gather results
        for future in futures:
            dfs.append(future.result())

    return dfs

# If the script is run directly, execute the function with the predefined spreadsheet name
if __name__ == "__main__":
    # Pre-fill this variable with the spreadsheet path and name
    spreadsheet_name = 'Glucose SELEX LOD with CA.xlsx'
    pstracetoinput(spreadsheet_name)
