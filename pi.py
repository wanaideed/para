import serial
import re
import RPi.GPIO as GPIO
import time
import csv
import os
from datetime import datetime

# Configure the serial port
ser = serial.Serial(
    port='/dev/ttyUSB0',          # Specify your port here (e.g., 'COM6' on Windows, '/dev/ttyUSB0' on Linux)
    baudrate=9600,        # Baud rate
    parity=serial.PARITY_NONE,  # No parity
    stopbits=serial.STOPBITS_ONE,  # One stop bit
    bytesize=serial.EIGHTBITS,  # 8 data bits
    timeout=1  # Read timeout in seconds
)

# GPIO pin configuration
relay_pins = {
    'first': 17,  # GPIO pin for the first condition / relay 1
    'second': 18,  # GPIO pin for the second condition / relay 2
    'third': 27,  # GPIO pin for the third condition / relay 3
    'fourth': 22  # GPIO pin for the fourth condition / relay 4
}

# Setup GPIO mode
GPIO.setmode(GPIO.BCM)
for pin in relay_pins.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # Initial state is OFF


# Function to create a new CSV file with the current date
def create_new_file():
    filename = datetime.now().strftime("%d%m%Y") + ".csv"
    if not os.path.isfile(filename):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["value", "datetime"])  # Write the header
    return filename


# Function to append data to the CSV file
def append_to_csv(filename, weight):
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([weight, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])


# Function to read the minimum weight threshold from min.txt
def read_min_threshold():
    try:
        with open("min.txt", "r") as file:
            value = float(file.read().strip())
            return value
    except (FileNotFoundError, ValueError):
        return 1.000


# Function to write the weight to MainWeight.txt
def write_to_main_weight(weight):
    with open("MainWeight.txt", "w") as file:
        file.write(f"{weight:.3f}")  # Write the weight in decimal format (3 decimal places)


# Function to read from the serial port continuously
def read_from_serial():
    current_filename = create_new_file()
    min_threshold = read_min_threshold()
    last_data_time = time.time()  # Track the last time data was received
    try:
        GPIO.output(relay_pins['first'], GPIO.LOW)
        GPIO.output(relay_pins['second'], GPIO.LOW)
        GPIO.output(relay_pins['third'], GPIO.LOW)
        GPIO.output(relay_pins['fourth'], GPIO.LOW)
        time.sleep(3)
        GPIO.output(relay_pins['first'], GPIO.HIGH)
        GPIO.output(relay_pins['second'], GPIO.HIGH)
        GPIO.output(relay_pins['third'], GPIO.HIGH)
        GPIO.output(relay_pins['fourth'], GPIO.HIGH)
        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()

                last_data_time = time.time() # Reset the idle timer when data is received
                # Turn off the buzzer if data is received
                GPIO.output(relay_pins['fourth'], GPIO.HIGH)  # Turn OFF buzzer

                if data:
                    match = re.search(r'[-+]?\d*\.\d+', data)
                    if match:
                        weight = float(match.group())
                        print(f"Weight: {data}")
                        write_to_main_weight(weight)

                        if weight > min_threshold:
                            print("Weight: Hijau")
                            GPIO.output(relay_pins['first'], GPIO.LOW)  # Turn ON relay for first condition
                            GPIO.output(relay_pins['second'], GPIO.HIGH)  # Turn OFF relay for second condition
                            GPIO.output(relay_pins['third'], GPIO.HIGH)  # Turn OFF relay for third condition
                            append_to_csv(current_filename, weight)  # Write to CSV file
                        elif weight <= min_threshold and weight > 0.100:
                            print("Weight: Merah")
                            GPIO.output(relay_pins['first'], GPIO.HIGH)  # Turn OFF relay for first condition
                            GPIO.output(relay_pins['second'], GPIO.LOW)  # Turn ON relay for second condition
                            GPIO.output(relay_pins['third'], GPIO.HIGH)  # Turn OFF relay for third condition
                        elif 0.000 <= weight <= 0.100:
                            print("Weight: Kuning")
                            GPIO.output(relay_pins['first'], GPIO.HIGH)  # Turn OFF relay for first condition
                            GPIO.output(relay_pins['second'], GPIO.HIGH)  # Turn OFF relay for second condition
                            GPIO.output(relay_pins['third'], GPIO.LOW)  # Turn ON relay for third condition
                        else:
                            print("Weight: Merah")  # Catch all other cases

                        # Turn on the fourth relay for 20 seconds and turn off if the weight changes
                        # if last_weight is None or last_weight != weight:
                        #     last_weight = weight
                        #     GPIO.output(relay_pins['fourth'], GPIO.LOW)  # Turn ON relay for 20 seconds
                        #     time.sleep(0.5)
                        #     GPIO.output(relay_pins['fourth'], GPIO.HIGH)  # Turn OFF relay

                        # Check if a new day has started to create a new CSV file
                        new_filename = datetime.now().strftime("%d%m%Y") + ".csv"
                        if new_filename != current_filename:
                            current_filename = create_new_file()

            if time.time() - last_data_time > 30:
                print("Idle")
                GPIO.output(relay_pins['fourth'], GPIO.LOW)  # Turn ON relay for the fourth condition (delay)
            # else:
            #     GPIO.output(relay_pins['fourth'], GPIO.HIGH)  # Turn OFF relay if not idle


    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        GPIO.cleanup()
        ser.close()

# Start reading from the serial port
read_from_serial()


