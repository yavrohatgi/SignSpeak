Content used:

BMI270 IMU datasheet: https://www.sparkfun.com/products/22398

BMI270 Micropython Library: https://github.com/jposada202020/MicroPython_BMI270

Micropython Installation: [to fill in]

19 Nov 2024: 
main.py is the file that is run on the Pico. If you need to indefinitely loop, make sure to set a large number of iterations instead of adding a while loop. The button is wired as a reset connection - it disconnects the Pico from your computer. 10kOhm resistors are needed on each I2C lines, as it's specification. 