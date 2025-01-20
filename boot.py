import bluetooth
import time
from machine import deepsleep, reset_cause, DEEPSLEEP_RESET, RTC

# Define fixed device name
device_name = "CHR000001"

# Toggles
USE_DEEP_SLEEP = False  # Set to True for deep sleep, False for time.sleep
USE_WHITELIST = True   # Set to True to enable the whitelist, False to track all devices
WHITELIST_PREFIXES = ["E4:B3:23"]  # List of address prefixes to filter devices   # Set to True to enable the whitelist, False to track all devices

# Configurable variables
INTER_SCAN_DURATION = 55  # Time in seconds between scans
SCAN_DURATION = 5000  # Duration of each scan in milliseconds
SCAN_WINDOW = 50  # BLE scan window in milliseconds

# Function to set the device's time
SSID = "Temporary WiFi"
PASSWORD = "password"




# RTC instance for date-time management
rtc = RTC()



# Function to save the current RTC time to non-volatile storage
def save_time_to_flash():
    """Save the current RTC time as epoch to a file for persistence."""
    try:
        current_time = rtc.datetime()
        epoch_time = time.mktime((
            current_time[0], current_time[1], current_time[2],
            current_time[4], current_time[5], current_time[6],
            current_time[3], 0  # Weekday (tm_wday), yearday ignored
        ))
        with open("rtc_time.txt", "w") as f:
            f.write(str(epoch_time))
        print(f"Saved epoch time to flash: {epoch_time}")
    except OSError as e:
        print(f"Error saving time to flash: {e}")

# Function to load the RTC time from non-volatile storage
def load_time_from_flash():
    """Load the saved epoch time from a file and set the RTC."""
    try:
        with open("rtc_time.txt", "r") as f:
            epoch_time = int(f.read().strip())
            tm = time.localtime(epoch_time)
            rtc.datetime((tm[0], tm[1], tm[2], 0, tm[3], tm[4], tm[5], 0))
            print(f"Loaded epoch time from flash: {epoch_time} -> RTC: {rtc.datetime()}")
    except OSError:
        print("No saved time found in flash. Using default time.")
    except ValueError:
        print("Invalid epoch format in flash. Resetting RTC.")



from machine import Pin
from time import sleep

# Define the pin where the LED is connected (adjust to your board)
led = Pin(8, Pin.OUT)

def blink_led(times, delay):
    """Blink the LED a specified number of times."""
    for _ in range(times):
        led.on()       # Turn the LED on
        sleep(delay)   # Wait
        led.off()      # Turn the LED off
        sleep(delay)   # Wait

def set_device_time_from_ntp():
    """Synchronize the RTC with NTP server using Wi-Fi and indicate with LED."""
    import network
    import ntptime

    # Connect to Wi-Fi
    station = network.WLAN(network.STA_IF)
    station.active(True)
    station.connect(SSID, PASSWORD)

    while not station.isconnected():
        print("Connecting to Wi-Fi...")
        blink_led(1, 0.5)  # Slow blink while connecting
        sleep(1)

    print("Connected to Wi-Fi!")
    print("Network config:", station.ifconfig())

    # Set NTP host
    ntptime.host = "time.google.com"

    try:
        # Sync time with NTP
        ntptime.settime()
        print("Time synchronized successfully!")
        current_time = time.localtime()
        print("Current time:", "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(*current_time[:6]))
        rtc.datetime((current_time[0], current_time[1], current_time[2], 0, current_time[3], current_time[4], current_time[5], 0))

        # Indicate success with fast blink
        blink_led(10, 0.2)
        led.off()  # Turn off LED after success
    except Exception as e:
        print(f"Failed to synchronize time: {e}")
        # Indicate failure with slow blink
        blink_led(5, 1)
        led.off()  # Turn off LED after failure
    finally:
        # Disable Wi-Fi to save power
        station.active(False)
        print("Wi-Fi disabled to conserve power.")

def create_adv_payload(name, services=None, manufacturer=None):
    """Create a custom advertising payload."""
    payload = bytearray()

    # Add flags (LE General Discoverable Mode, BR/EDR Not Supported)
    payload += b'\x02\x01\x06'

    # Add complete local name
    if name:
        name_bytes = name.encode('utf-8')
        payload += bytes([len(name_bytes) + 1, 0x09]) + name_bytes

    # Add 16-bit service UUIDs (if provided)
    if services:
        for uuid in services:
            payload += bytes([3, 0x03]) + uuid.to_bytes(2, 'little')

    # Add manufacturer data (if provided)
    if manufacturer:
        payload += bytes([len(manufacturer) + 1, 0xFF]) + manufacturer

    return payload

# Function to format address
def format_addr(addr):
    """Format the address as a human-readable string."""
    return ':'.join('{:02X}'.format(b) for b in addr)

# Function to parse whitelist from file
def load_whitelist(filename):
    """Load a whitelist of addresses from a file."""
    try:
        with open(filename, "r") as f:
            return set(line.strip().upper() for line in f if line.strip())
    except OSError:
        print(f"Error: Unable to read {filename}.")
        return set()

# Function to parse advertisement data for the device name
def parse_name(adv_data):
    """Extract known fields from the advertisement data."""
    i = 0
    while i < len(adv_data):
        length = adv_data[i]
        if length == 0:
            break
        field_type = adv_data[i + 1]
        field_data = adv_data[i + 2:i + 1 + length]

        # Check for Complete or Shortened Local Name
        if field_type in (0x09, 0x08):  # Complete or Shortened Local Name
            return field_data.decode('utf-8')
        i += 1 + length
    return None

# Main function to scan and log strongest RSSI
def track_strongest_signals(ble, log_file, whitelist):
    import gc
    print("[DEBUG] Starting track_strongest_signals...")
    print(f"[DEBUG] Memory available at start: {gc.mem_free()} bytes")

    print(f"Starting periodic scanning using {'deep sleep' if USE_DEEP_SLEEP else 'idle sleep'}...")

    # Check if waking up from deep sleep
    if USE_DEEP_SLEEP and reset_cause() == DEEPSLEEP_RESET:
        print("Waking up from deep sleep...")

    # Dictionary to track the strongest RSSI per device
    strongest_signals = {}
    if USE_WHITELIST:
        strongest_signals = {addr: None for addr in whitelist}
    else:
        strongest_signals.clear()

    gc.collect()
    print(f"[DEBUG] Memory after clearing signals: {gc.mem_free()} bytes")

    def scan_callback(event, data):
        """Callback to handle BLE scan results."""
        if event == 5:  # BLE_SCAN_RESULT event
            addr_type, addr, adv_data, rssi, scan_response = data

            # Convert memoryviews to bytes
            formatted_addr = format_addr(addr)

            # Process only whitelisted devices if whitelist is enabled
            if not USE_WHITELIST or any(formatted_addr.startswith(prefix) for prefix in WHITELIST_PREFIXES):
                # Update strongest RSSI if necessary (closer to 0 is stronger)
                if formatted_addr not in strongest_signals or strongest_signals[formatted_addr] is None or rssi > strongest_signals[formatted_addr]:
                    strongest_signals[formatted_addr] = rssi

    # Set the BLE IRQ callback
    ble.irq(scan_callback)

    try:
        print("[DEBUG] Entering main loop...")
        while True:
            # Start scanning for the configured duration with reduced scan window
            print("Scanning for devices...")
            print("[DEBUG] Starting BLE scan...")
            ble.gap_scan(SCAN_DURATION, 10000, SCAN_WINDOW)  # Configurable scan duration and window
            print("[DEBUG] Scan complete. Sleeping for scan duration...")
            time.sleep(SCAN_DURATION / 1000)  # Wait for the scan to complete

            # Save the strongest signals to the log file
            with open(log_file, "a") as f:
                gc.collect()
                print(f"[DEBUG] Memory before logging: {gc.mem_free()} bytes")
                for addr, rssi in strongest_signals.items():
                    if rssi is not None:
                        # Get the current time from RTC
                        current_time = rtc.datetime()
                        timestamp = f"{current_time[0] % 100:02}{current_time[1]:02}{current_time[2]:02}{current_time[4]:02}{current_time[5]:02}{current_time[6]:02}"
                        # Write to file: address, RSSI, and time
                        print(f"[DEBUG] Logging: {addr},{rssi},{timestamp}")
                        f.write(f"{addr},{rssi},{timestamp}\n")

            # Clear the dictionary for the next scan
            if USE_WHITELIST:
                strongest_signals = {addr: None for addr in whitelist}
            else:
                strongest_signals.clear()

            # Handle idle or deep sleep
            if USE_DEEP_SLEEP:
                print("Entering deep sleep...")
                deepsleep(INTER_SCAN_DURATION * 1000)  # Deep sleep for the configured duration
            else:
                print(f"Idling for {INTER_SCAN_DURATION} seconds...")
                time.sleep(INTER_SCAN_DURATION)  # Idle between scans

    except KeyboardInterrupt:
        print("Stopping scanning and logging...")
        ble.gap_scan(None)  # Stop scanning
        ble.irq(None)  # Remove callback

# Initialize BLE
ble = bluetooth.BLE()
ble.active(True)

# Load the whitelist
# Initialize whitelist (used for address prefix matching)
whitelist = set()
if USE_WHITELIST:
    whitelist = load_whitelist("whitelist.txt")
    if not whitelist:
        print("Warning: Whitelist is empty. No devices will be tracked.")

# Define advertising data
service_uuids = [0x180D, 0x181C]  # Example UUIDs
manufacturer_data = b'\x01\x02\x03\x04'  # Manufacturer data

adv_data = create_adv_payload(device_name, services=service_uuids, manufacturer=manufacturer_data)

# Start advertising
ble.gap_advertise(100000, adv_data)
print(f"Broadcasting as '{device_name}'...")

# Log file path
log_file = "bt_strongest_signals.txt"

# Set initial time (example: 2025-01-01 12:00:00)
set_device_time_from_ntp()

# Start tracking strongest signals
track_strongest_signals(ble, log_file, whitelist)

