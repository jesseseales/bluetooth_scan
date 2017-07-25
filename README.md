# bluetooth_scan

## Assumptions and Requirements
- Raspberry Pi with Python 3.
- Pexpect python module, numpy, matplotlib.
- Bluetooth is on and no other bluetoothctl session is running 
- Note: it might be necessesary to run `apt-get install libffi-dev` then `pip3 install cairocffi`

## Usage
This program is intended to be run on a Raspberry Pi and runs indefinitely, creating plots of discoverable bluetooth devices by executing "bluetoothctl" commands.
This program aims to keep track of only bluetooth devices passing by the raspberry pi, so if a device is detected consistently for static_time amount of time, it is added to an ignore_list where it will be ignored for the rest of the scanning.
Also, since bluetooth devices aren't automatically removed when they move out of range, this program will manually remove devices after time_diff amount of time. If the device is still active, it will reappear on the next scan. Otherwise, it will not continue to be counted.
Because of the static_time and time_diff aspects of this program, in order to begin accurately reading device counts, it is necessary to run the program for at least static_time amount of time to allow for static devices to be added to the ignore_list.
