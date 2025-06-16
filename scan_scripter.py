from plot_swv import perform_calibration_scan, partial_scan, full_scan, plot_curve, prep_for_scan, setup
import time
from teensy_comm import TeensyController
#from pstrace_processing import swv_processing, pstrace_separation

SCAN_SEQUENCE = 'scan_script.txt'

#def csv_plotter(path)
    # plot a csv
    

def open_txt(tc):
    print('running open_txt')
    repeat = 0
    full_scans = []
    partial_scans = []
    chpwe = []
    with open(SCAN_SEQUENCE, 'r') as file:
        lines = file.read().splitlines()
    print(lines)
    if lines[0].find("epeat") != -1:
        repeat = int(lines[0].split()[1]) # Repeat x, gets x-val
        lines = lines[1:] #removes first line from list
        print(lines)
    for i in range(repeat+1): #
        for line in lines:
            #print(line)    
            if line.find("full") != -1: #full
                x = full_scan()
                full_scans.append(x[0])
                peak, baseline = x[1], x[2]
            elif line.find("partial") != -1: #partial
                partial_scans.append(partial_scan(peak, baseline))
            elif line.startswith("("): #(4, 5)
                t = tuple(int(x.strip()) for x in line.strip("()").split(","))
                chip, we = t
                chpwe.append(t)
                print(tc.send_command(chip, we))
            elif line.startswith("rest:"): #rest: 100
                time.sleep(int(line.split(":")[1].strip()))
    print(partial_scans)
    print('TEST')
    print(full_scans)
    print('TEST')
    print(chpwe)
    return partial_scans, full_scans, chpwe

'''
def data_compiler(partial_scans, full_scans, chpwe) #4 full, 4 partial per chpwe
    for i in range(len(chpwe)):
        for scan in full_scans:
            write row(chpwe, 'full', voltage, values)
            write row (chpwe, 'full', current, values
'''           
        

def plot(partial, full):
    for x, y in partial, full:
        plot_curve(x, y)

def main():
    setup()
    #prep_for_scan()
    tc = TeensyController()
    conn_status = tc.connect()
    print(conn_status)
    open_txt(tc)
    #plot(open_txt(tc))
    tc.disconnect()

if __name__ == "__main__":
    main()

# Example Syntax:
'''
Repeat 1 # repeats once, so total of two runs
(4,5) # switches to chp 4, we 5
full # does full scan. MUST do full scan before partial scan
partial #does partial scan

'''


