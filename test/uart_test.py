"""
Connect ESP32 via UART with GPIO pin 23 and 24.
Since it is not default UART pin, we use PiGPIO module for mapping.
Downside is that it cannot maintain 115200Hz communication -> use 57600Hz
Note: You need to set ESP32 baudrate accordingly to 57600Hz
"""

import pigpio
import time

# UART settings
pi = pigpio.pi()
TX = 23
RX = 24


def main():
    """
    Reads UART pin without parsing.
    Expected results: prints chunks of string bytes from ESP32
    """
    pi.bb_serial_read_open(RX, 57600)

    while True:
        count, data = pi.bb_serial_read(RX)
        if count:
            print(data)
        time.sleep(0.01)

if __name__ == "__main__":
    main()
