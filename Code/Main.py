#Reference Link: GitHub = https://github.com/rravivarman/RaspberryPi/tree/master/MAX30102
#Reference Link: Git Hub = https://github.com/tutRPi/Raspberry-Pi-Heartbeat-Pulse-Sensor.git

import time
from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306
import sys
import smbus
import max30102
import requests
import hrcalc
import Adafruit_DHT

from pulsesensor import Pulsesensor
import time

p = Pulsesensor()
p.startAsyncBPM()
 
DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4
# ThingSpeak Data (Endpoint, API Key)
API_ENDPOINT = "https://api.thingspeak.com/update"
API_KEY = "WSTSSEVV70D3S07V"

# MAX30102 pulse oximeter

# Set up the OLED screen
disp = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_address=0x3C)
disp.begin()

# Clear the screen
disp.clear()
disp.display()

# Create a blank image for the OLED screen
image = Image.new("1", (disp.width, disp.height))
draw = ImageDraw.Draw(image)

# Load a font to use for displaying the data
font = ImageFont.load_default()

m = max30102.MAX30102()
heartrate = 0
oxygen = 0
          
def temperatureData():
    humidity, temperature = Adafruit_DHT.read(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        print("Temp={0:0.1f}C Humidity={1:0.1f}%".format(temperature, humidity))
    
    time.sleep(1);
    return temperature
# ----------------------------Pulse Sensor--------------------------------------------    
def pulsedata():
    try:
            bpm = p.BPM
            if bpm > 0:
                print("BPM: %d" % bpm)
                bpm=int(bpm)
                time.sleep(1)
            
    except:
                        p.stopAsyncBPM()
    return bpm
#------------------------------MAX10302-----------------------------------------------
while True:
    red, ir = m.read_sequential()

    hr, hrb, sp, spb = hrcalc.calc_hr_and_spo2(ir, red)
    temp=temperatureData()
    pulse= pulsedata()
    print("-------------------------------------------------------------")
    print("HR detected:", hrb)
    print("SpO2 detected:", spb)

    if hrb == True and hr != -999:
        heartrate = int(hr)

        
    if spb == True and sp != -999:
        oxygen = int(sp)
        print("SpO2:", oxygen)
        
    #--------------------------OLED Display-------------------------------------------    
   
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)
    draw.text((0, 0), f"Temp: {temp} C", font=font, fill=255)
    draw.text((0, 10), f"BPM: {pulse}" , font=font, fill=255)
    draw.text((0, 20), f"SpO2: {oxygen}", font=font, fill=255)
    disp.image(image)
    disp.display()
    
    #--------------------------thing speak data----------------------------------------
    payload = {'api_key': API_KEY, 'field1': temp, 'field2': pulse, 'field3': oxygen}
    response = requests.post(API_ENDPOINT, params=payload)

	        
        
    
	        
