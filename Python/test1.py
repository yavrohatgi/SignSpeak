from machine import I2C, Pin
import time

# I2C configuration
I2C_SCL_PIN = 1  # SCL on GPIO1
I2C_SDA_PIN = 0  # SDA on GPIO2
BMI270_ADDRESS = 0x68  # Device address

# Initialize I2C
i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN), freq=400000)

# Read function
def read_register(reg, length=1):
    try:
        return i2c.readfrom_mem(BMI270_ADDRESS, reg, length)
    except OSError as e:
        print(f"Error reading register {reg}: {e}")
        return None

# Write function
def write_register(reg, value):
    try:
        i2c.writeto_mem(BMI270_ADDRESS, reg, bytearray([value]))
    except OSError as e:
        print(f"Error writing register {reg}: {e}")

# Example: Initialize the BMI270
def initialize_bmi270():
    # Example setup for BMI270 (refer to the datasheet for specific registers)
    write_register(0x7E, 0x11)  # Example: Enter normal mode for accelerometer
    write_register(0x7E, 0x15)  # Example: Enter normal mode for gyroscope
    time.sleep(0.1)

def to_signed(val, bits):
    """Convert an unsigned integer to signed."""
    if val >= (1 << (bits - 1)):
        val -= (1 << bits)
    return val

def read_accelerometer_data():
        acc_data = read_register(0x0C, 6)  # Adjust register address as needed
        if acc_data:
                # Assuming 16-bit signed values with 4g sensitivity
                sensitivity = 4096  # Adjust sensitivity as per datasheet
                ax = to_signed(int.from_bytes(acc_data[0:2], "little"), 16) / sensitivity
                ay = to_signed(int.from_bytes(acc_data[2:4], "little"), 16) / sensitivity
                az = to_signed(int.from_bytes(acc_data[4:6], "little"), 16) / sensitivity
                print(f"Accelerometer (X, Y, Z): {ax:.2f}, {ay:.2f}, {az:.2f} g")
        else:
                print("No data read from accelerometer.")

def main():
        initialize_bmi270()  # Ensure initialization runs once
        for i in range(100):
                print(i)
                try:
                        read_accelerometer_data()
                except Exception as e:
                        print(f"Error: {e}")
                        break  # Exit loop on error
                time.sleep(0.5)

# Run the main loop
main()