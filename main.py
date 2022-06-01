"""
Things to-be done:
Watchdog to reset the system if it freezes,
Code for an external temperature sensor,
Code to read a Potentiometer or PWM output/activation signal for an external circuit to control a fan,
Better code cohesion,
Code for use of an external LED as I plan on putting the board in a box,
Create boot screen bitmap,
Create special character bitmaps.

THIS CODE IS UNDER NO LISCENSE.
"""


import utime
import _thread
from ssd1306 import SSD1306_I2C
from machine import Pin, ADC, I2C

#########################
class Stack:
    """The Stack implementation for my furnace"""
    def __init__(self) -> None:
        self.STACK = []
        self.MUTEX = _thread.allocate_lock()
        
    def push(self, arg) -> None: 
        self.STACK.append(arg)
         
    
    def pop(self):
        if self.isEmpty() == True:
            return False
        a = self.STACK[-1]
        self.STACK.remove(self.STACK[-1]) 
        return a

    def peek(self):
        """return last element but do not remove it"""
        if self.isEmpty() == True:
            self.MUTEX.release()
            return False
        return self.STACK[-1]
       
    def isEmpty(self) -> bool:
        """is the stack empty?"""
        if len(self.STACK) == 0:
            return True 
      
    def typePeek(self) -> type:
        return type(self.STACK[-1])
    

class Furnace(Stack):
    
    CONVERSION = 3.3/(65535) #ADC reading Conversion factor
    
    def __init__(self, i2c:tuple, oled: tuple, adc: int ):
        #stack init
        super().__init__()
        
        #variable declarations
        self.i2c = i2c
        
        #I2C bus set-up
        self.interface = I2C(self.i2c[0],
                             scl=machine.Pin(self.i2c[1]),
                             sda=machine.Pin(self.i2c[2]),
                             freq=self.i2c[3])
        
        #screen init
        self.oled = SSD1306_I2C(oled[0],
                                oled[1],
                                self.interface)
        
        #Periferal init        
        self.tempSensor = machine.ADC(adc)
        self.obLed = machine.Pin(25, Pin.OUT)
        
        
        #calls the start of the program
        print("started")
        self.start()
        
    #worker functions
    
    def start(self):
        self.obLed.high()
        utime.sleep(1)
        self.obLed.low()
        """Start the threads"""
        _thread.start_new_thread(self._update, ())
        self.update()
    
    def clean(self):
        """turn everything off when KeyboardInterrupt is found"""
        self.oled.fill(0)
        self.oled.show()
        self.obLed.low()
    
    def _update(self):
        """second thread of Execution"""
        #print("thread started") #debug code
        self.count = 0
        while True:
            self.MUTEX.acquire()
            self.obLed.high()
            try:
                if not super().isEmpty():
                    _temp = super().pop()
                    _cTemp = round(27 - (_temp - 0.706)/0.001721, 2)
                    #print(f"{_cTemp}C") #debug again
                    
                    
                    """
                    These values will change when I implement a config file
                    or a class system for selecting temperature ranges
                    """
                    self.oled.text(f"{_cTemp}C", 5, 5)
                    if _cTemp > 17:
                        self.oled.text("Too hot!", 5, 15)
                    if _cTemp < 17 and _cTemp >= 14:
                        self.oled.text("Temp Okay!", 5, 15)
                    if _cTemp < 14:
                        self.oled.text("Too Cold!", 5, 15)
                    self.count = self.count + 1
                    self.oled.text("."*((self.count%3)+1), 5, 25)
                    self.oled.show()
            finally:
                self.obLed.low()
                self.MUTEX.release()
                self.oled.fill(0)
                 
                
                
                
    def update(self):
        """Main Thread of Execution"""
        try:
            """Try/Finally to stop second thread when Keyboard interrupt"""
            while True:
                #print("update fired")
                super().push(self.tempSensor.read_u16()*Furnace.CONVERSION) #put temp reading on the stack
                utime.sleep(1) #sleep so it doesn't flood the stack with values
                
        finally:
            #clean-up code for keyboard interupts
            print("exiting thread")
            self.clean()
            _thread.exit()
            
                    
                
if __name__ == "__main__":
    """Values passed as tuples so that they will not be changed"""
    fur = Furnace((0, 1, 0, 200000),(128,32), 4)