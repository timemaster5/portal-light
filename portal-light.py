import usb.core
import usb.util
import time
import random

#(0, 0, 0),       # Black (LED off)
SATURATED_COLORS = [
    (255, 0, 0),     # Red
    (0, 255, 0),     # Green
    (0, 0, 255),     # Blue
    (255, 255, 0),   # Yellow
    (255, 0, 255),   # Magenta
    (0, 255, 255),   # Cyan
    (255, 128, 0),   # Orange
    (128, 0, 255),   # Purple
    (0, 255, 128),   # Spring Green
    (255, 0, 128),   # Pink
    (128, 255, 0),   # Chartreuse
    (0, 128, 255),   # Azure
    (255, 255, 255), # White
    (128, 128, 128), # Medium Gray (somewhat saturated)
    (255, 64, 64),   # Light Red
]

def send_report(dev, data):
    assert len(data) == 32
    bmRequestType = 0x21
    bRequest = 0x09
    wValue = 0x0200
    wIndex = 0
    dev.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data)

def activate_portal(dev, on=True):
    val = 0x01 if on else 0x00
    data = [0x41, val] + [0x00]*30
    send_report(dev, data)

def ready_portal(dev):
    data = [0x52] + [0x00]*31
    send_report(dev, data)

def set_led_color(dev, r, g, b):
    data = [0x43, r, g, b] + [0x00]*28
    send_report(dev, data)

def main():
    VID = 0x1430
    PID = 0x0150
    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if dev is None:
        print("Portal not found")
        return
    if dev.is_kernel_driver_active(0):
        dev.detach_kernel_driver(0)
    dev.set_configuration()
    time.sleep(0.1)

    activate_portal(dev, True)
    set_led_color(dev, 255, 255, 255)  # start white

    endpoint_address = 0x81
    packet_size = 32

    last_value_1 = None
    last_change_time_1 = None
    last_accepted_change_time_1 = 0
    color_changed_for_value_1 = None

    led_off = False  # State whether the LED is off

    try:
        while True:
            try:
                raw_data = dev.read(endpoint_address, packet_size, timeout=500)
                raw_data = list(raw_data)
                print("Raw data read:", raw_data)
            except usb.core.USBError as e:
                print("USB read error:", e)
                raw_data = [0]*packet_size

            value_0 = raw_data[0]
            value_1 = raw_data[1]
            now = time.time()

            if value_1 == 0:
                if not led_off:
                    set_led_color(dev, 0, 0, 0)
                    print("Value at index 0 is 0 - LED turned off")
                    led_off = True
                # Ignore further changes while LED is off
                last_value_1 = None
                last_change_time_1 = None
                color_changed_for_value_1 = None
            else:
                # LED should be on (if it was off)
                if led_off:
                    # Set default white color
                    set_led_color(dev, 255, 255, 255)
                    led_off = False

                # Work with value at index 1 (color change)
                if value_1 != last_value_1:
                    if (now - last_accepted_change_time_1) >= 0.1:
                        last_value_1 = value_1
                        last_change_time_1 = now
                        last_accepted_change_time_1 = now
                        color_changed_for_value_1 = None
                        print(f"Value at index 1 changed to {value_1}, waiting 0.1 seconds for stability...")
                    else:
                        print(f"Change to value {value_1} ignored, too fast change (less than 0.1s from last)")

                else:
                    if last_change_time_1 is not None and (now - last_change_time_1) >= 0.1:
                        if color_changed_for_value_1 != value_1:
                            r, g, b = random.choice(SATURATED_COLORS)
                            set_led_color(dev, r, g, b)
                            print(f"LED color changed to RGB({r},{g},{b}) due to value {value_1} after 0.1 seconds of stable value")
                            color_changed_for_value_1 = value_1

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()
