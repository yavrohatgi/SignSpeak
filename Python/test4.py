from machine import I2C, Pin

# Use the correct SDA and SCL pins for your setup
i2c = I2C(0, sda=Pin(4), scl=Pin(5))

print("Scanning I2C bus...")
devices = i2c.scan()

if devices:
    print(f"I2C devices found: {[hex(device) for device in devices]}")
else:
    print("No I2C devices found. Check connections.")