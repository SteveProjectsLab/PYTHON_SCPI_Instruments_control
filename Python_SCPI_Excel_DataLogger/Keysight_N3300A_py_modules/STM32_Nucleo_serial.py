import serial
import time
import sys
        
class Stm32_serial:

    #builder
    def __init__(self, port="COM5", baud=115200):
        try:
            #attributes
            self.port = port 
            self.baud = baud
            self.ser = serial.Serial(port=self.port,baudrate=self.baud)
        except:
            print("\nFailed to connect the stm32")
            print("\nclosing the program...")
            time.sleep(3)
            sys.exit()
            
    def checkPortOpen(self):
        if self.ser.isOpen():                    
            print("stm32 connected on "+self.ser.name + '!\n')
        else:
            print('stm32 connection error...')
           
    def write(self,data):
         self.ser.write(data)
         
    def read(self):
        data = str(self.ser.readline().strip()).strip('b\'') #leggi la scheda Nucleo
        return data
    
    def close(self):
        self.ser.close()

    def flush(self):
        self.ser.flush()