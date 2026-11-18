# portal-light

Turns an unused Skylanders Portal of Power (USB, `1430:0150`) into a lamp: when a figure is
placed on the portal, its LED switches to a random saturated colour.

## Run

```
pip install pyusb
sudo python3 portal-light.py
```

Root (or a udev rule for `1430:0150`) is needed to detach the kernel HID driver.
