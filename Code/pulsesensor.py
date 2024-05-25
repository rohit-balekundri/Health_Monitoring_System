#Reference Link: Git Hub = https://github.com/tutRPi/Raspberry-Pi-Heartbeat-Pulse-Sensor.git

"""
This Raspberry Pi's MCP3008 analog-to-digital converter uses a pulse sensor attached to a Python class named Pulsesensor to measure heartbeats. The MCP3008 library is assumed to be provided by the code.

Three techniques exist for the Pulsesensor class:
By setting the channel to read from on the MCP3008, establishing an instance of the MCP3008 class, and initializing variables necessary to calculate the heart rate, the _init_ method initializes the pulse sensor.

The primary procedure, getBPMLoop, receives the pulse sensor signal, analyzes the signal to pinpoint the timing of heartbeats, and then calculates the heart rate (measured in beats per minute, or BPM). Until the thread is halted, this function continues in an endless loop.
The getBPMLoop method is executed by a new thread created by the startAsyncBPM method.

The BPM is set to 0 via the stopAsyncBPM function, which also ends the thread that startAsyncBPM initiated.
The getBPMLoop method uses a set of variables to analyze the signal and calculate the heart rate.
The getBPMLoop method is executed by a new thread that is started by the startAsyncBPM method. This enables other code to continue running while the pulse sensor operates in the background.

The BPM is set to 0 via the stopAsyncBPM function, which also ends the thread that startAsyncBPM initiated. When the pulse sensor is no longer required, this can be used to stop it and release system resources.

"""

import time
import threading
from MCP3008 import MCP3008

class Pulsesensor:
    def __init__(self, channel = 0, bus = 0, device = 0):
        self.channel = channel
        self.BPM = 0
        self.adc = MCP3008(bus, device)

    def getBPMLoop(self):
        # init variables
        rate = [0] * 10         
        sampleCounter = 0       
        lastBeatTime = 0        
        P = 512                 
        T = 512                 
        thresh = 525            
        amp = 100               
        firstBeat = True        
        secondBeat = False      

        IBI = 600               
        Pulse = False            
        lastTime = int(time.time()*1000)
        
        while not self.thread.stopped:
            Signal = self.adc.read(self.channel)
            currentTime = int(time.time()*1000)
            
            sampleCounter += currentTime - lastTime
            lastTime = currentTime
            
            N = sampleCounter - lastBeatTime

            # find the peak and trough of the pulse wave
            if Signal < thresh and N > (IBI/5.0)*3:     
                if Signal < T:                          
                    T = Signal                           

            if Signal > thresh and Signal > P:
                P = Signal

            # signal surges up in value every time there is a pulse
            if N > 250:                                 
                if Signal > thresh and Pulse == False and N > (IBI/5.0)*3:       
                    Pulse = True                        
                    IBI = sampleCounter - lastBeatTime  
                    lastBeatTime = sampleCounter        

                    if secondBeat:                      
                        secondBeat = False;             
                        for i in range(len(rate)):      
                          rate[i] = IBI

                    if firstBeat:                       
                        firstBeat = False;              
                        secondBeat = True;              
                        continue

                    # keep a running total of the last 10 IBI values  
                    rate[:-1] = rate[1:]                
                    rate[-1] = IBI                     
                    runningTotal = sum(rate)            

                    runningTotal /= len(rate)           
                    self.BPM = 60000/runningTotal       

            if Signal < thresh and Pulse == True:       
                Pulse = False                           
                amp = P - T                             
                thresh = amp/2 + T                      
                P = thresh                              
                T = thresh

            if N > 2500:                                
                thresh = 512                            
                P = 512                                 
                T = 512                                 
                lastBeatTime = sampleCounter                   
                firstBeat = True                        
                secondBeat = False                      
                self.BPM = 0

            time.sleep(0.005)
            
        
    # Start getBPMLoop routine which saves the BPM in its variable
    def startAsyncBPM(self):
        self.thread = threading.Thread(target=self.getBPMLoop)
        self.thread.stopped = False
        self.thread.start()
        return
        
    # Stop the routine
    def stopAsyncBPM(self):
        self.thread.stopped = True
        self.BPM = 0
        return
    
