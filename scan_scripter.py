from plot_swv import perform_calibration_scan, perform_partial_scans, plot_curve, prep_for_scan, setup
import time
from RPi_Teensy_comm import teensy_comm

FILENAME = 'scan_script.txt'

def open_txt(tc):
    repeat = 0
    full_scans = []
    partial_scans = []
    file = open(FILENAME, mode = 'r', encoding = 'utf-8-sig')
    lines = file.readline()
    if lines[0].find("epeat") != -1:
        repeat = int(lines[0].split()[1]) # Repeat x, gets x-val
        lines = lines[1:] #removes first line from list
    for i in range(repeat+1): #
        for line in lines:    
            if line.find("full") != -1: #full
                x = perform_calibration_scan()
                full_scans.append(x[0])
                peak, baseline = x[1], x[2]
            elif line.find("partial") != -1: #partial
                partial_scans.append(perform_partial_scans(peak, baseline))
            elif line.startswith("("): #(4, 5)
                t = tuple(int(x.strip()) for x in line.strip("()").split(","))
                tc.send_command(t[0], t[1])
            elif line.startswith("rest:"): #rest: 100
                time.sleep(int(line.split(":")[1].strip()))
    return partial_scans, full_scans

def plot(partial, full):
    for x, y in partial, full:
        plot_curve(x, y)

def main():
    setup()
    prep_for_scan()
    tc = teensy_comm.TeensyController()
    tc.connect()
    plot(open_txt(tc))
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


