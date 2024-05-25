#Reference Link: GitHub = #Reference Link: Git Hub = https://github.com/tutRPi/Raspberry-Pi-Heartbeat-Pulse-Sensor.git

"""
This Python class allows for SPI bus-based communication with an MCP3008 analog-to-digital converter (ADC). 
Here is a thorough breakdown of the techniques:
The constructor method, _init_(self, bus=0, device=0), initializes the object with the bus and device numbers to be used for the SPI connection. 
Bus 0 and device 0 are the default selections. Additionally, it generates a SpiDev object for SPI communication and increases the SPI bus's top speed to 1 MHz.
open(self) - This function opens the SPI connection by invoking the object's open method and limits the SPI bus's top speed to 1 MHz.
read(self, channel=0) - This method retrieves the relevant digital value from the MCP3008 ADC by reading the analog voltage on a designated channel. 
If the channel argument is not supplied, it defaults to 0. 
Created using the SpiDev xfer2 technique, the instruction is sent to the MCP3008 to read from the chosen channel. 
The response is then processed to obtain the digital value.
close(self) - This method calls the close method of the SpiDev object to terminate the SPI connection.
A Python interface for using the SPI bus on Linux systems is provided via the SpiDev module. 
An 8-channel, 10-bit analog-to-digital converter that uses the SPI bus for communication is called the MCP3008 ADC. 
In a Python program, the MCP3008 class can be used to read analog values from the MCP3008 ADC utilizing the SPI bus. 
It offers a simple interface for interacting with the ADC and transforming analog voltage into a digital value.

"""

from spidev import SpiDev

class MCP3008:
    def __init__(self, bus = 0, device = 0):
        self.bus, self.device = bus, device
        self.spi = SpiDev()
        self.open()
        self.spi.max_speed_hz = 1000000 # 1MHz

    def open(self):
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = 1000000 # 1MHz
    
    def read(self, channel = 0):
        cmd1 = 4 | 2 | (( channel & 4) >> 2)
        cmd2 = (channel & 3) << 6

        adc = self.spi.xfer2([cmd1, cmd2, 0])
        data = ((adc[1] & 15) << 8) + adc[2]
        return data
            
    def close(self):
        self.spi.close()
