#Reference Link: Git Hub: https://github.com/rravivarman/RaspberryPi/tree/master/MAX30102

"""
This code connects a Raspberry Pi to the MAX30102 Pulse Oximeter and Heart Rate Sensor. 
It has functions to read data from the device, initialize and configure the device, and reset the device's software.
A low-power, combined pulse oximeter and heart-rate monitor sensor is the MAX30102. 
To detect pulse oximetry and heart rate signals, it incorporates two LEDs, a photodetector, improved optics, and low-noise analog signal processing.
The code configures the device by filling its registers with predefined values from the comments. 
The interrupt register is then read, cleared, and the device's interrupt settings are set. 
Additionally, it sets the device's sampling rate and LED pulse width.
The reset() function can be used to restart the device and erase all settings. 
The gadget can be turned off using the shutdown() function. 
Any configuration value for the device can be modified using the set_config() function.
The device's FIFO buffer is read by the read_fifo() method, which then transforms the data into pulse and oxygen saturation values. 
Both red and infrared data can be output by the device, and the code includes routines to read both. 
The information is given back as a tuple that includes the red and infrared values.

"""

from __future__ import print_function
from time import sleep

import RPi.GPIO as GPIO
import smbus


I2C_WRITE_ADDR = 0xAE
I2C_READ_ADDR = 0xAF

# register address-es
REG_INTR_STATUS_1 = 0x00
REG_INTR_STATUS_2 = 0x01

REG_INTR_ENABLE_1 = 0x02
REG_INTR_ENABLE_2 = 0x03

REG_FIFO_WR_PTR = 0x04
REG_OVF_COUNTER = 0x05
REG_FIFO_RD_PTR = 0x06
REG_FIFO_DATA = 0x07
REG_FIFO_CONFIG = 0x08

REG_MODE_CONFIG = 0x09
REG_SPO2_CONFIG = 0x0A
REG_LED1_PA = 0x0C

REG_LED2_PA = 0x0D
REG_PILOT_PA = 0x10
REG_MULTI_LED_CTRL1 = 0x11
REG_MULTI_LED_CTRL2 = 0x12

REG_TEMP_INTR = 0x1F
REG_TEMP_FRAC = 0x20
REG_TEMP_CONFIG = 0x21
REG_PROX_INT_THRESH = 0x30
REG_REV_ID = 0xFE
REG_PART_ID = 0xFF

MAX_BRIGHTNESS = 255


class MAX30102():
    # by default, this assumes that physical pin 7 (GPIO 4) is used as interrupt
    # by default, this assumes that the device is at 0x57 on channel 1
    def __init__(self, channel=1, address=0x57, gpio_pin=7):
        print("Channel: {0}, address: 0x{1:x}".format(channel, address))
        self.address = address
        self.channel = channel
        self.bus = smbus.SMBus(self.channel)
        self.interrupt = gpio_pin
        
     
        GPIO.setup(self.interrupt, GPIO.IN) 
        self.reset()

        sleep(1)  # wait 1 sec

        # read & clear interrupt register (read 1 byte)
        reg_data = self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_1, 1)
        self.setup()
       

    def shutdown(self):
        
        #Shutdown the device.
        
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [0x80])

    def reset(self):
        
        #Reset the device, this will clear all settings, so after running this, run setup() again.
        
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [0x40])

    def setup(self, led_mode=0x03):
       
        
        self.bus.write_i2c_block_data(self.address, REG_INTR_ENABLE_1, [0xc0])
        self.bus.write_i2c_block_data(self.address, REG_INTR_ENABLE_2, [0x00])

      
        self.bus.write_i2c_block_data(self.address, REG_FIFO_WR_PTR, [0x00])
        
        self.bus.write_i2c_block_data(self.address, REG_OVF_COUNTER, [0x00])
       
        self.bus.write_i2c_block_data(self.address, REG_FIFO_RD_PTR, [0x00])

        
        self.bus.write_i2c_block_data(self.address, REG_FIFO_CONFIG, [0x4f])

        
        self.bus.write_i2c_block_data(self.address, REG_MODE_CONFIG, [led_mode])
        
        self.bus.write_i2c_block_data(self.address, REG_SPO2_CONFIG, [0x27])

  
        self.bus.write_i2c_block_data(self.address, REG_LED1_PA, [0x24])
        
        self.bus.write_i2c_block_data(self.address, REG_LED2_PA, [0x24])
        
        self.bus.write_i2c_block_data(self.address, REG_PILOT_PA, [0x7f])

    
    def set_config(self, reg, value):
        self.bus.write_i2c_block_data(self.address, reg, value)

    def read_fifo(self):
        """
        This function will read the data register.
        """
        red_led = None
        ir_led = None

        # read 1 byte from registers (values are discarded)
        reg_INTR1 = self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_1, 1)
        reg_INTR2 = self.bus.read_i2c_block_data(self.address, REG_INTR_STATUS_2, 1)

        # read 6-byte data from the device
        d = self.bus.read_i2c_block_data(self.address, REG_FIFO_DATA, 6)

        red_led = (d[0] << 16 | d[1] << 8 | d[2]) & 0x03FFFF
        ir_led = (d[3] << 16 | d[4] << 8 | d[5]) & 0x03FFFF

        return red_led, ir_led

    def read_sequential(self, amount=100):
        """
        This function will read the red-led and ir-led `amount` times.
        This works as blocking function.
        """
        red_buf = []
        ir_buf = []
        for i in range(amount):
            while(GPIO.input(self.interrupt) == 1):
                # wait for interrupt signal, which means the data is available
                pass

            red, ir = self.read_fifo()

            red_buf.append(red)
            ir_buf.append(ir)

        return red_buf, ir_buf
