#*** hello_ASL.py ***

import board
import busio
import adafruit_tca9548a
import adafruit_ssd1306

# Set up I2C on the BeagleBone Black (SCL/SDA are P9_19 / P9_20 by default on I2C2)
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the TCA9548A multiplexer
tca = adafruit_tca9548a.TCA9548A(i2c)

# Scan devices on channel 7
print([hex(device_address) for device_address in tca[7].scan()])

# Access channel 7
i2c_channel_7 = tca[7]

# Initialize the OLED display (adjust width/height to your display)
WIDTH = 128
HEIGHT = 64
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c_channel_7)

# Clear the display
oled.fill(0)
oled.show()

# Display some text using the default font
oled.text("Hello, ASL!", 0, 0, 1)
oled.show()
