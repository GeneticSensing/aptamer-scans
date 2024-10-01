import pandas as pd

# Pre-fill this variable with the spreadsheet name
spreadsheet_name = 'Glucose SELEX LOD with CA.xlsx'

def pstracetoinput(spreadsheet_name):
    read_file = pd.read_excel(spreadsheet_name)
    title = read_file.columns.tolist()

    titleCleaned = []
    titleDuplicated = []

    for t in title:
        if "Unnamed" not in t:
            titleCleaned.append(t)
            titleDuplicated.append(t)
            titleDuplicated.append(t)

    for i in range(len(titleCleaned)):
        read_file = pd.read_excel(spreadsheet_name)
        read_file.columns = titleDuplicated
        read_file = read_file[titleCleaned[i]]
        read_file = read_file.iloc[1:]
        # absolute value of currents
        read_file.iloc[:,1] = read_file.iloc[:,1]*(-1) 
        read_file.loc[-1] = ["Time [s]", "Current [uA]"]
        read_file.index = read_file.index + 1  
        read_file = read_file.sort_index()
        read_file.to_csv(titleCleaned[i] + ".csv", index=None, header=None, encoding="utf-8")

# If the script is run directly, execute the function with the predefined spreadsheet name
if __name__ == "__main__":
    pstracetoinput(spreadsheet_name)
