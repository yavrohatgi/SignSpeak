import serial

# Open serial connection (adjust the port as needed)
ser = serial.Serial('/dev/cu.usbmodem1101', 115200, timeout=1)

# TXT file setup
txt_filename = 'imu_data.txt'

print("Waiting for serial data... Pxess Ctrl+C to stop.\n")

try:
    with open(txt_filename, 'w') as txtfile:  # Open in write mode (overwrite each run)
        while True:
            # Read a line from serial
            line = ser.readline().decode('utf-8').strip()

            # Skip empty lines
            if not line:
                continue

            # Print to console
            print(line)

            # Write to file
            txtfile.write(line + '\n')
            txtfile.flush()  # Force immediate write to file

            # Stop when "Training data collection complete." appears
            if "Training data collection complete." in line:
                print("\n🚀 Training complete. Closing file...")
                break  # Stop reading from serial

except KeyboardInterrupt:
    print("\n🚀 Stopping logging and closing file...")
    ser.close()