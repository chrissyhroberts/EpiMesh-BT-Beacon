# EpiMesh-BT-Beacon
A Bluetooth Beacon Network for logging proximities of entities across time via Bluetooth - ESP32-C3 based.

![su](https://github.com/user-attachments/assets/149aeffa-d5d1-435f-98e3-9b3d922b8cdf)


## Summary

Many problems in epidemiology and one health centre around the potential for events (i.e. transmission of infectious diseaes) to occur when two entities (any combination people, vectors, livestock, places) come in to close proximity. Transmission/event risk is generally higher with prolonged proximity. 

Researchers often try to use GPS devices to measure proximity, but the functional limit of around 10m accuracy in GPS means that entities with the same geolocation might actually be as far apart as 30m, which is uninformative.

This project provides code that can turn a cheap (~£5) WiFi/Bluetooth development board in to a bluetooth beacon and logger for proximity and duration of interactions. Because it's based on bluetooth it works within 10m. Caveat is that bluetooth doesn't pass through human bodies very well, so signal averaging may be useful. 

In this prototype design, which is scalable to a large number of beacons in a 'mesh', each device connects to a temporary WiFi signal, sets the real time clock, then disconnects from WiFi. It then broadcasts its own MAC address via bluetooth. Meanwhile it periodically scans for nearby bluetooth signals, identifies which (if any) are relevant from a whitelist, then logs the signal strength (averaged across a period of seconds). The other devices do the same thing, and across time build a mesh data set of proximity data that can be used to identify instances when two, three or more devices came in to proximity. 

The data are logged to a file on the device's flash memory with datetime, MAC address and signal strength. 

## Use Cases

### A group of people who interact  
<img width="508" alt="Screenshot 2025-01-20 at 17 35 52" src="https://github.com/user-attachments/assets/cf000033-0672-4b55-8bcd-e1a108b7b23b" />  

### Entities crossing a geofence  
<img width="510" alt="Screenshot 2025-01-20 at 17 36 19" src="https://github.com/user-attachments/assets/0d8c26b3-2b02-4e1e-b09b-36e6935c8f0a" />   

This could also have a double layered fence to establish direction of travel.  

### Interactions between livestock, wildlife and burrows  
<img width="507" alt="Screenshot 2025-01-20 at 17 37 16" src="https://github.com/user-attachments/assets/e0d23518-060f-4ca3-a4c4-fb8166653652" />  

### Utilisation of public services, like boreholes or public toilets  
<img width="500" alt="Screenshot 2025-01-20 at 17 37 44" src="https://github.com/user-attachments/assets/2fa11f40-1b19-4389-8450-d91e154d5337" />  

Under this model, we could also flag utilisation by people carrying bluetooth enabled smart-devices, rather than ESP32-based beacons  


## Hardware

* ESP32-C3 Development Board (WiFi/Bluetooth)  
I bought three for £16.99 on Amazon  
https://www.amazon.co.uk/dp/B0DMN6VKNN?ref_=pe_27063361_487360311_302_E_DDE_dt_1  

* USB-C cable with data & power  

## Setup

Out of the box, the boards need to be wiped and also need firmware adding.

Download the firmware from https://micropython.org/download/ESP32_GENERIC/  
I used v1.24.1 : https://micropython.org/resources/firmware/ESP32_GENERIC-20241129-v1.24.1.bin  

Open terminal and add the esp control tools, which can be used to flash firmware

```
pip3 install esptool
```
Check the installation with

```
 esptool.py
```
This should show you the help file. If it does, the installation is good. 

Next Plug in a device via the USB cable. If you see a dialog asking for permission to mount the device, accept it.
List connected devices with

```
ls /dev/cu.*  
```

This should show you something like

> /dev/cu.usbmodem2101

Next, erase the device with

```
esptool.py --chip esp32c3 --port /dev/cu.usbmodem2101 erase_flash
```
It should say something like this

>esptool.py v4.8.1  
Serial port /dev/cu.usbmodem2101  
Connecting....  
Chip is ESP32-C3 (QFN32) (revision v0.4)  
Features: WiFi, BLE, Embedded Flash 4MB (XMC)  
Crystal is 40MHz  
MAC: e4:b3:23:d3:9d:64  
Uploading stub...  
Running stub...  
Stub running...  
Erasing flash (this may take a while)...  
Chip erase completed successfully in 16.2s  
Hard resetting via RTS pin...  

Make a note of the device's MAC address, you'll need this later

Next add the new firmware with 

```
esptool.py --chip esp32c3 --port /dev/cu.usbmodem2101 --baud 460800 write_flash -z 0x0 ESP32_GENERIC_C3-20241129-v1.24.1.bin
```
Note that `/dev/cu.usbmodem2101` should match the address you saw when you listed the connected devices.

It should display something like this 

>esptool.py v4.8.1  
Serial port /dev/cu.usbmodem2101  
Connecting....  
Chip is ESP32-C3 (QFN32) (revision v0.4)  
Features: WiFi, BLE, Embedded Flash 4MB (XMC)  
Crystal is 40MHz  
MAC: e4:b3:23:d3:9d:64  
Uploading stub...  
Running stub...  
Stub running...  
Changing baud rate to 460800  
Changed.  
Configuring flash size...  
Flash will be erased from 0x00000000 to 0x001b2fff...  
Compressed 1779264 bytes to 1083505...  
Wrote 1779264 bytes (1083505 compressed) at 0x00000000 in 13.7 seconds (effective 1042.8 kbit/s)...  
Hash of data verified.  
Leaving...  
Hard resetting via RTS pin...


Next open **Thonny** https://thonny.org/
Configure the interpreter for Micropython (ESP32)
You should see the files on the micropython device in the lower 'files' section. 


Replace the `boot.py` script with the one from this repo. 

Edit the top of the file to add your wifi network and password
Decide if you're using a whitelist. If so, set the prefixes to match those in your list of MAC addresses

`WHITELIST_PREFIXES = ["E4:B3:23"]  # List of address prefixes to filter devices`
`WHITELIST_PREFIXES = ["E4:B3:23","E4:B6:E3"]  # List of address prefixes to filter devices`

Save and test by running the script. You should see some useful feedback

>MPY: soft reboot  
Broadcasting as 'CHR000001'...  
Connecting to Wi-Fi...  
Connecting to Wi-Fi...  
Connecting to Wi-Fi...  
Connecting to Wi-Fi...  
Connected to Wi-Fi!  
Network config: ('192.168.87.25', '255.255.255.0', '192.168.87.1', '192.168.87.1')  
Time synchronized successfully!  
Current time: 2025-01-20 16:25:31  
Wi-Fi disabled to conserve power.  
[DEBUG] Starting track_strongest_signals...  
[DEBUG] Memory available at start: 88128 bytes  
Starting periodic scanning using idle sleep...  
[DEBUG] Memory after clearing signals: 92512 bytes  
[DEBUG] Entering main loop...  
Scanning for devices...  
[DEBUG] Starting BLE scan...  
[DEBUG] Scan complete. Sleeping for scan duration...  
[DEBUG] Memory before logging: 92080 bytes  
[DEBUG] Logging: E4:B3:23:D3:76:26,-89,250120162540  
[DEBUG] Logging: E4:B3:23:D5:EC:42,-72,250120162540  
Idling for 55 seconds...  

Finally, repeat for all your devices. Update the whitelist so that all mesh devices are included. 

That's it!




