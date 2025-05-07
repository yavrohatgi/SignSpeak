import serial # install it using pip3 install pyserial

ser = serial.Serial('/dev/cu.usbmodem1101', 115200, timeout=1)  # Open serial port, change port as needed
txt_filename = 'raw_data.txt'                                   # Output filename  

print("Waiting for serial data!!!\n")

try:
    with open(txt_filename, 'w') as txtfile:              # Open in write mode (overwrites existing file)
        while True:
            line = ser.readline().decode('utf-8').strip() # Read a line from serial
            if not line:                                  # Skip empty lines
                continue 
            print(line)                                   # Print to console

            txtfile.write(line + '\n')                    # Write to file
            txtfile.flush()                               # Force immediate write to file

            if "Training data collection complete." in line: # Stop when training is complete
                print("\nTraining complete!!!")
                break

except KeyboardInterrupt:                                  # Catch Ctrl+C ie user interrupt
    print("\nStopping logging and closing file!!!")
    ser.close()