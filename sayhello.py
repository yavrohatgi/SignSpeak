import serial
import time

port = '/dev/tty.usbmodem1101'  # Update if your device path changes
baud_rate = 115200  # Default for MicroPython or CircuitPython

try:
    # Open the serial connection
    pico = serial.Serial(port, baud_rate, timeout=1)
    time.sleep(2)  # Wait for the connection to stabilize

    # Send a command to the Pico (e.g., if using MicroPython REPL)
    pico.write(b'print("Hello from Pico!")\n')

    # Read the response
    response = pico.readlines()
    for line in response:
        print(line.decode().strip())

    pico.close()

except serial.SerialException as e:
    print(f"Error: {e}")

pico.close()