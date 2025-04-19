import serial
import lgpio
import time

# Serial Defines
PORT = "/dev/ttyUSB2"
BAUDRATE = 115200


# GPIO setup
FULL_CARD_POWER_OFF = 16
CHIP = 0  # Default GPIO chip on Raspberry Pi 5

# Open GPIO chip
h = lgpio.gpiochip_open(CHIP)

# Set up pin as an output
lgpio.gpio_claim_output(h, FULL_CARD_POWER_OFF, 0)  # Default LOW


def shutdown_module():
    ser = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=1)
    try:
        ser.write(b"AT+CFUN=0\r\n")  # Send AT command for shutdown
        response = ser.readline().strip()

        if response == b"OK":
            lgpio.gpio_write(h, FULL_CARD_POWER_OFF, 0)  # Set pin LOW
            time.sleep(1)
        else:
            print("Module Shutdown Failed")

    except serial.SerialException as e:
        print(f"SERIAL SHUTDOWN ERROR: {e}")
    except Exception as e:
        print(f"UNEXPECTED SHUTDOWN ERROR: {e}")


def power_on_module():
    try:
        lgpio.gpio_write(h, FULL_CARD_POWER_OFF, 1)  # Set pin HIGH
    except Exception as e:
        print(f"UNEXPECTED POWER_ON ERROR: {e}")


def main():
    power_on_module()
    # try:
    #     power_on_module()
    # finally:
    # shutdown_module()
    lgpio.gpiochip_close(h)  # Cleanup GPIO


if __name__ == "__main__":
    main()
