#! /usr/bin/python

import sys, getopt, re, pexpect, time, datetime, pexpect
import numpy as np
from matplotlib import pyplot as plt

class Bluetoothctl:
    
    ignore_list = set() # insert bluetooth IDs of other pis here
    
    def __init__(self):
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
        self.child.send("devices\n")
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
            update = re.search(".*((DEL)|(CHG)|(NEW)).*Device .*..:..:..:..:..:..", device) # only detect new devices
            match = re.search("..:..:..:..:..:..", device) 
            #if match != None and update != None: # exclude update messages
            if update == None and match != None:
                bt_id = match.group(0) # parse the regex match
                if bt_id not in self.ignore_list: # filter out ignore_list IDs
                    device_list.append(bt_id)
        return device_list
    
    # attempt to remove a device from the devices list
    # if the device is still active, this will not stop it from being re-added
    # otherwise, this will avoid counting it repeatedly
    def removeDevice(self, device_id):
        self.child.send("remove " + device_id + "\n")
        try:
            index = self.child.expect(["Device has been removed", "not available"])
            if index == 0:
                print("removing device " + device_id + ". If it is still active, it will reappear")
            else:
                print("Could not remove device", device_id)
        except TIMEOUT:
            print("Timeout while trying to remove device:", device_id)
    
    def exit(self):
        self.child.send("scan off\n")
        self.child.expect("bluetooth")
        self.child.send("exit\n")
        
    def usage(self):
        print(" bluetooth_scan scans indefinitely and plots new bluetooth devices to a graph every 60 seconds")
    
if __name__ == "__main__":
    bt = Bluetoothctl()
    try:
        opts, args = getopt.getopt(sys.argv[1:],"h",["help"])
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
    
    static_time = datetime.timedelta(minutes=30) # threshold for considering a device as being static
    time_diff = datetime.timedelta(minutes=5) # threshold for keeping a device on the device list
    devices = {}
    device_count = []
    i = 0
    
    while(True):
        
        updated_list = bt.refreshDevices()
        for id in updated_list:
            if id not in devices:
                devices[id] = datetime.datetime.now()
            elif datetime.datetime.now() - devices[id] > static_time:
                # consider as a static device
                print("Removing static device:", id)
                del devices[id]
                bt.ignore_list.add(id)
            elif datetime.datetime.now() - devices[id] > time_diff:
                # execute command to remove the device
                # if the device is still within reach, it will reconnect
                bt.removeDevice(id)
                
        device_count.append(len(devices))
        if i%60==0:
            # print devices found, save to graph
            plt.plot(device_count)
            plt.ylabel("# of new bluetooth devices")
            plt.xlabel("seconds since starting")
            print("saving to graph")
            plt.savefig("plot" + str(i) + ".jpg", bbox_inches = 'tight')
        
        time.sleep(1)
        i+=1
        
    bt.exit()
