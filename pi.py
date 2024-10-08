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
    'hijau': 17,  # GPIO pin for the first condition / relay 1 hijau
    'merah': 18,  # GPIO pin for the second condition / relay 2 merah
    'kuning': 27,  # GPIO pin for the third condition / relay 3
    'buzzer': 22  # GPIO pin for the fourth condition / relay 4
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
def read_merah_threshold():
    try:
        with open("merah.txt", "r") as file:
            value = float(file.read().strip())
            return value
    except (FileNotFoundError, ValueError):
        return 1.000

# Function to read the minimum weight threshold from min.txt
def read_buzer_threshold():
    try:
        with open("buzzer.txt", "r") as file:
            value = float(file.read().strip())
            return value
    except (FileNotFoundError, ValueError):
        return 10


# bunyi brpe second
def read_kuning_threshold():
    try:
        with open("kuning.txt", "r") as file:
            value = int(file.read().strip())
            return value
    except (FileNotFoundError, ValueError):
        return 10


# bunyi brpe second
def read_hijau_threshold():
    try:
        with open("hijau.txt", "r") as file:
            value = file.read()
            return value
    except (FileNotFoundError, ValueError):
        return 10


# Function to write the weight to MainWeight.txt
def write_to_main_weight(weight):
    with open("MainWeight.txt", "w") as file:
        file.write(f"{weight:.3f}")  # Write the weight in decimal format (3 decimal places)


# Function to read from the serial port continuously
def read_from_serial():
    current_filename = create_new_file()
    merah_threshold = read_merah_threshold()
    buzzer_threshold = read_buzer_threshold()
    kuning_threshold = read_kuning_threshold()
    hijau_threshold = read_hijau_threshold()
    modeRelay = ""

    print("hijau_threshold", hijau_threshold)
    print("kuning_threshold", kuning_threshold)
    print("buzzer_threshold", buzzer_threshold)
    print("merah_threshold", merah_threshold)
    last_data_time = time.time()  # Track the last time data was received
    try:
        GPIO.output(relay_pins['hijau'], GPIO.LOW)
        GPIO.output(relay_pins['merah'], GPIO.LOW)
        GPIO.output(relay_pins['kuning'], GPIO.LOW)
        GPIO.output(relay_pins['buzzer'], GPIO.LOW)
        time.sleep(3)
        GPIO.output(relay_pins['hijau'], GPIO.HIGH)
        GPIO.output(relay_pins['merah'], GPIO.HIGH)
        GPIO.output(relay_pins['kuning'], GPIO.HIGH)
        GPIO.output(relay_pins['buzzer'], GPIO.HIGH)


        while True:
            if ser.in_waiting > 0:
                data = ser.readline().decode('utf-8').strip()


                last_data_time = time.time() # Reset the idle timer when data is received


                if data:
                    match = re.search(r'[-+]?\d*\.\d+', data)
                    if match:
                        weight = float(match.group())
                        print(f"Weight: {data}")
                        write_to_main_weight(weight)
                        append_to_csv(current_filename, weight)  # Write to CSV file

                        if weight > merah_threshold:
                            modeRelay = "hijau"
                            if hijau_threshold == "on":
                                print("HIJAU ON")
                                GPIO.output(relay_pins['hijau'], GPIO.LOW)
                                GPIO.output(relay_pins['merah'], GPIO.HIGH)
                                GPIO.output(relay_pins['kuning'], GPIO.HIGH)
                                GPIO.output(relay_pins['buzzer'], GPIO.HIGH)
                            else:
                                print("HIJAU OFF")
                                GPIO.output(relay_pins['hijau'], GPIO.HIGH)
                                GPIO.output(relay_pins['merah'], GPIO.HIGH)
                                GPIO.output(relay_pins['kuning'], GPIO.HIGH)
                                GPIO.output(relay_pins['buzzer'], GPIO.HIGH)
                        elif weight <= merah_threshold and weight > 0.000:
                            modeRelay = "merah"
                            print("Weight: Merah")
                            GPIO.output(relay_pins['hijau'], GPIO.HIGH)  # Turn OFF relay for first condition
                            GPIO.output(relay_pins['merah'], GPIO.LOW)  # Turn ON relay for second condition
                            GPIO.output(relay_pins['kuning'], GPIO.HIGH)  # Turn OFF relay for third condition

                            GPIO.output(relay_pins['buzzer'], GPIO.HIGH)  # Turn OFF relay for third condition
                        elif 0.000 == weight:
                            modeRelay = "kuning"
                            print("Weight: Kuning")
                            GPIO.output(relay_pins['hijau'], GPIO.HIGH)  # Turn OFF relay for first condition
                            GPIO.output(relay_pins['merah'], GPIO.HIGH)  # Turn OFF relay for second condition
                            GPIO.output(relay_pins['kuning'], GPIO.LOW)  # Turn ON relay for third condition
                            GPIO.output(relay_pins['buzzer'], GPIO.HIGH)  # Turn OFF relay for third condition

                        if weight <= buzzer_threshold and weight > 0.000:
                            modeRelay = modeRelay+"buzzer"
                            GPIO.output(relay_pins['buzzer'], GPIO.LOW)
                            time.sleep(3)
                            GPIO.output(relay_pins['buzzer'], GPIO.HIGH)
                        else:
                            GPIO.output(relay_pins['buzzer'], GPIO.HIGH)

                        # Check if a new day has started to create a new CSV file
                        new_filename = datetime.now().strftime("%d%m%Y") + ".csv"
                        if new_filename != current_filename:
                            current_filename = create_new_file()

            if time.time() - last_data_time > int(kuning_threshold):    ## value second
                if modeRelay == "merahbuzzer":
                    GPIO.output(relay_pins['merah'], GPIO.HIGH)
                elif modeRelay == "merah":
                    GPIO.output(relay_pins['merah'], GPIO.LOW)
                # print("Idle")
                # GPIO.output(relay_pins['hijau'], GPIO.HIGH)  # Turn OFF relay for first condition
                # GPIO.output(relay_pins['merah'], GPIO.HIGH)  # Turn OFF relay for second condition
                GPIO.output(relay_pins['kuning'], GPIO.LOW)  # Turn ON relay for the fourth condition (delay)
                # GPIO.output(relay_pins['buzzer'], GPIO.HIGH)  # Turn OFF relay for third condition



    except KeyboardInterrupt:
        print("Stopped by user")
    finally:
        GPIO.cleanup()
        ser.close()

# Start reading from the serial port
read_from_serial()


