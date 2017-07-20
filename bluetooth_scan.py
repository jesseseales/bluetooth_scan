#! /usr/bin/python

import sys, getopt, re, pexpect, time, subprocess, datetime
import numpy as np
from matplotlib import pyplot as plt
from pexpect import * # pip install pexpect

class Bluetoothctl:
    
    ignore_list = [] # insert bluetooth IDs of other pis here
    
    def __init__(self):
        out = subprocess.check_output("sudo rfkill unblock bluetooth", shell = True)
        self.child = pexpect.spawn("bluetoothctl")
        bt_index = self.child.expect(["bluetooth", pexpect.EOF])
        if bt_index != 0:
            print("Failed to start bluetoothctl...exiting")
            sys.exit(2)
        
    # execute "scan on"
    def scan(self):
        self.child.send("scan on\n")
        scan_index = self.child.expect(["Discovering: yes", pexpect.EOF])
        self.child.expect("bluetooth")
        if scan_index == 0:
            print("Scan successfully turned on")
        else:
            print("Error starting scan...exiting")
            sys.exit(2)
    
    def refreshDevices(self):
        device_list = []
        self.child.send(" \n")
        index = self.child.expect(["bluetooth", pexpect.EOF])
        if index == 0:
            output_str = self.child.before.decode("utf-8")
            device_list = self.parseDeviceOutput(output_str, device_list)
        else:
            print("Could not refresh devices...exiting")
            sys.exit(2)
        return device_list
        
    def parseDeviceOutput(self, output_str, device_list):
        bt_devices = output_str.split("\n")
        msg = ""
        for device in bt_devices:
            # only pay attention to mesages with NEW in them
            update = re.search(".*NEW.*Device .*..:..:..:..:..:..", device) # only detect new devices
            match = re.search("..:..:..:..:..:..", device) 
            #if match != None and update != None: # exclude update messages
            if update != None and match != None:
                bt_id = match.group(0) # parse the regex match
                if bt_id not in self.ignore_list: # filter out ignore_list IDs
                    device_list.append(bt_id)
                    print("New device found:", bt_id)
        return device_list
    
    def exit(self):
        self.child.send("scan off\n")
        self.child.expect("bluetooth")
        self.child.send("exit\n")
        
    def usage(self):
        print(" bluetooth_scan scans indefinitely and plots new bluetooth devices to a graph every 60 seconds")
    
if __name__ == "__main__":
    bt = Bluetoothctl()
    try:
        opts, args = getopt.getopt(sys.argv[1:],"ht:",["help"])
    except getopt.GetoptError as err:
        print(err)
        bt.usage()
        sys.exit(2)
    if opts:
        for o in opts:
            if o in ("-h","--help"):
                bt.usage()
                sys.exit(0)
            
    print("Launching bluetooth")
    bt.scan()
              
    devices = []
    time_list = []
    device_count = []
    i = 0
    while(True):
        #scan for 60 seconds
        for j in range(60):
            devices += bt.refreshDevices()
            time.sleep(1)
            i+=1
        
        # time is currently being unused bc of the difficulty to display on graph
        t = datetime.datetime.now()
        time_list.append(t.minute)
        
        device_count.append(len(devices))
        del devices[:] # clear list of devices
        
        # print devices found, save to graph
        print(device_count)
        plt.plot(device_count)
        plt.ylabel("# of new bluetooth devices")
        plt.xlabel("minutes since starting")
        print("saving to graph")
        plt.savefig("plot" + str(i) + ".jpg", bbox_inches = 'tight')
        
    bt.exit()
