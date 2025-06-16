from plot_swv import perform_calibration_scan, partial_scan, full_scan, plot_curve, prep_for_scan, setup
import time
from teensy_comm import TeensyController
import csv
import os
#from pstrace_processing import swv_processing, pstrace_separation

SCAN_SEQUENCE = 'scan_script.txt'

#def csv_plotter(path)
    # plot a csv
    

def open_txt(tc):
    print('running open_txt')
    repeat = 0
    full_scans = [[], [], [], [], []]
    partial_scans = [[], [], [], []]
    chpwe = []
    peaks = []
    peaks_partial = []
    with open(SCAN_SEQUENCE, 'r') as file:
        lines = file.read().splitlines()
    print(lines)
    if lines[0].find("epeat") != -1:
        repeat = int(lines[0].split()[1]) # Repeat x, gets x-val
        lines = lines[1:] #removes first line from list
        print(lines)
    a = -1 #bc we always start with a teensy message
    for i in range(repeat+1): #
        for line in lines:
            #print(line)    
            if line.find("full") != -1: #full
                x = full_scan()
                print(a)
                full_scans[a].append(x[0])
                peak, baseline = x[1], x[2]
                peaks.append([peaks,baseline])
            elif line.find("partial") != -1: #partial
                x = partial_scan(peak, baseline)
                partial_scans[a].append(x[0])
                peaks = x[1]
                peaks_partial.append(peaks)
            elif line.startswith("("): #(4, 5)
                t = tuple(int(x.strip()) for x in line.strip("()").split(","))
                chip, we = t
                chpwe.append(t)
                a = a+1
                print(tc.send_command(chip, we))
            elif line.startswith("rest:"): #rest: 100
                time.sleep(int(line.split(":")[1].strip()))
    print(partial_scans)
    print('TEST')
    print(full_scans)
    print('TEST')
    print(chpwe)
    return partial_scans, full_scans, chpwe, peaks, peaks_partial


def data_compiler(partial_scans, full_scans, chpwe, peak, peaks_partial): #4 full, 4 partial per chpwe
    csv_path = os.path.abspath(os.path.join('output', 'summary.csv'))
    peak_csv_path = os.path.abspath(os.path.join('output', 'peaks.csv'))
    with open(csv_path, 'w') as f1, open(peak_csv_path, 'w') as f2:
        writer1 = csv.writer(f1)
        writer2 = csv.writer(f2)
        writer2.writerow(['Chp', 'We', 'Peak', 'Baseline'])
        writer1.writerow(['Chp', 'We', 'Scan Type', 'Axis', 'Values'])
        for i in range(len(chpwe)):
            for scan in full_scans[i]:
                x = [chpwe[i][0], chpwe[i][1], 'full', 'voltage']
                x.extend(scan[0])
                writer1.writerow(x)
                x = [chpwe[i][0], chpwe[i][1], 'full', 'current']
                x.extend(scan[1])
                writer1.writerow(x)
            for x in range(len(full_scans[i])):
                writer2.writerow([chpwe[i][0], chpwe[i][1], 'full', str(peak[x][0][0][-1]), peak[x][1]])
            for x in range(len(partial_scans[i])):
                writer2.writerow([chpwe[i][0], chpwe[i][1], 'partial', str(peaks_partial[x])])
            for scan in partial_scans[i]:
                x=[chpwe[i][0], chpwe[i][1], 'partial', 'voltage']
                x.extend(scan[0])
                writer1.writerow(x)
                x = [chpwe[i][0], chpwe[i][1], 'partial', 'current']
                x.extend(scan[1])
                writer1.writerow(x)          
        

def plot(partial, full):
    for x, y in partial, full:
        plot_curve(x, y)

def main():
    setup()
    #prep_for_scan()
    tc = TeensyController()
    conn_status = tc.connect()
    print(conn_status)
    partial, full, chpwe, peak, peaks_partial = open_txt(tc)
    #plot(open_txt(tc))
    tc.disconnect()
    data_compiler(partial, full, chpwe, peak, peaks_partial)

if __name__ == "__main__":
    main()

# Example Syntax:
'''
Repeat 1 # repeats once, so total of two runs
(4,5) # switches to chp 4, we 5
full # does full scan. MUST do full scan before partial scan
partial #does partial scan

'''


