Program your board using the esptool.py program, found [here](https://github.com/espressif/esptool).

If you are putting MicroPython on your board for the first time then you should
first erase the entire flash using:

```bash
esptool.py --chip esp32c6 --port /dev/ttyUSB0 erase_flash
```

From then on program the firmware starting at address 0x0:

```bash
esptool.py --chip esp32c6 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x0 ESP32_GENERIC_C6-20240602-v1.24.0.bin
```