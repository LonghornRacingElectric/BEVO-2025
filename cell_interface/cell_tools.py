import serial
import RPi.GPIO as GPIO
import time

# Serial Defines
PORT = '/dev/ttyUSB2'
BAUDRATE = 115200
ser = serial.Serial(port=PORT, baudrate=BAUDRATE, timeout=1)

# GPIO setup
FULL_CARD_POWER_OFF = 16
GPIO.setmode(GPIO.BCM)
GPIO.setup(FULL_CARD_POWER_OFF, GPIO.OUT)


def shutdown_module():
    try:
            ser.write(b'AT+CFUN=0\r\n') #send byte code for AT+CFUN=0 (shutdown)
            response = ser.readline()
            if response == "OK":
                GPIO.output(FULL_CARD_POWER_OFF, GPIO.LOW)
                time.sleep(1)
            else:
                print("Module Shutdown Failed")
    except serial.SerialException as e:
        print(f"SERIAL SHUTDOWN ERROR: {e}") 
    except Exception as e:
        print(f"UNEXPECTED SHUTDOWN ERROR: {e}")
        
def power_on_module():
    try:
        GPIO.output(FULL_CARD_POWER_OFF, GPIO.HIGH)
    except Exception as e:
        print(f"UNEXPECTED POWER_ON ERROR: {e}")
     
def main():
    # try:
    #     power_on_module()
    # finally:
        shutdown_module()
        GPIO.cleanup()
        
if __name__=='__main__':
    main()