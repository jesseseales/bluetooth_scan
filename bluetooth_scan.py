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
        
    # execute "devices" to retrieve current device list
    def refreshDevices(self, device_list):
        self.child.send("devices\n")
        index = self.child.expect(["bluetooth", pexpect.EOF])
        if index == 0:
            #print("before:", self.child.before)
            output_str = self.child.before.decode("utf-8")
            device_list = self.parseDeviceOutput(output_str, device_list)
        else:
            print("Could not refresh devices...exiting")
            sys.exit(2)

        return device_list
        
    def parseDeviceOutput(self, output_str, device_list):
        bt_devices = output_str.split("Device ")

        msg = ""
        for device in bt_devices:
            # ignore scan update message - i.e. [DEL], [NEW], or [CHG]
            # because device list will always be updated
            update = re.match(".+((CHG)|(NEW)|(DEL)|(RSSI)).+", device)
            match = re.match("..:..:..:..:..:..", device) 
            if match != None and update == None: # exclude update messages
                msg = "device"
                bt_id = match.group(0) # parse the regex match
                if bt_id not in self.ignore_list: # filter out ignore_list IDs
                    device_list.add(bt_id)
            else:
                msg = "update"
        #print number of changes / devices
        if (len(bt_devices)-1 != 1):
            msg = msg + "s"
            print(len(bt_devices)-1, msg)
        return device_list
    
    def exit(self):
        self.child.send("scan off\n")
        self.child.expect("bluetooth")
        self.child.send("exit\n")
        
    def usage(self):
        print(" bluetooth_scan scans for 60 seconds and plots available bluetooth devices to a graph\n",
              "Optional flags:\n",
              "-t --timeout [seconds]\tscan for t seconds\n",
              "-h --help\t\tshows this message\n")
    
if __name__ == "__main__":
    bt = Bluetoothctl()
    t = -1
    try:
        opts, args = getopt.getopt(sys.argv[1:],"ht:",["help","timeout"])
    except getopt.GetoptError as err:
        print(err)
        bt.usage()
        sys.exit(2)
    if opts:
        for o,a in opts:
            if o in ("-h","--help"):
                bt.usage()
                sys.exit(0)
            elif o in ("-t", "--timeout"):
                t = int(a)
                if t < 0:
                    print("t must be a non-negative integer")
                    sys.exit(0)
                else:
                    t = int(a)
            
    print("Launching bluetooth")
    bt.scan()
    devices = set()
    time_density = []
    if t > 0:
        # using a timeout
        for i in range(0,t):
            devices = bt.refreshDevices(devices)
            t = datetime.datetime.now()
            time_density.append( [t,len(devices)] )
            i+=1
            time.sleep(1)
            
        fig,ax = plt.subplots()
        ax.plot([x[1] for x in time_density], '-b')
        ax.set_xticklabels([x[0] for x in time_density])
        plt.xticks(rotation=90)
        plt.savefig("plot.png", bbox_inches = 'tight')
        
    else:
        # continually check for non-pi bluetooth devices and log count
        i = 0
        while(True):
            devices = bt.refreshDevices(devices)
            t = datetime.datetime.now()
            time_density.append( [t,len(devices)] )
            time.sleep(1)
            i+=1
            
            if i%60==0: # update graph every 60 seconds
                fig,ax = plt.subplots()
                print("plotting:",[x[1] for x in time_density])
                ax.plot([x[0] for x in time_density], [x[1] for x in time_density], '-b')
                plt.xticks(rotation=90)
                ax.set_ylabel("# of bluetooth devices")
                plt.savefig("plot.png", bbox_inches = 'tight')
                
        bt.exit()
