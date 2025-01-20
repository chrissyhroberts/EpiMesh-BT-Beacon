# EpiMesh-BT-Beacon
A Bluetooth Beacon Network for logging proximities of entities across time via Bluetooth - ESP32-C3 based.

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




