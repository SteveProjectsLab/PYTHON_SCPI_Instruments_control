import serial
import time
import sys
        
class ELN3300ASerial:

    
   
    
    #builder
    def __init__(self, port="COM5", baud=9600, parity=False, flowControl=False):
        self.port = port
        try:
            #attributes
            self.port = port 
            self.baud = baud
            self.parity = parity
            self.flowControl = False
            self.ser = serial.Serial(#see "programming guide" - pag 16
                    port=self.port,
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=5,         #Set a read timeout value in seconds.
                    xonxoff=False,      #software flow control
                    rtscts=False,       #hardware (RTS/CTS) flow control.
                    dsrdtr=False        #hardware (DSR/DTR) flow control.
                    #write_timeout      #Set a write timeout value in seconds.
                    #inter_byte_timeout #Inter-character timeout, None to disable (default).
            )
        except:
            print("\nFailed to connect the electronic load...")
            print("\nclosing the program...")
            time.sleep(3)
            sys.exit()
            
    

    def checkPortOpen(self,cmd):
        if self.ser.isOpen():               
            print("load  connected on "+self.ser.name + '!\n')
            #self.ser.write(b'*IDN?\n')   #ask to identify
            self.ser.write(cmd.deviceInfo()) 
            response=self.ser.readline().decode()
            print('Device info: '+ response )
            cmd.input_off() 
        else:
            print('\nconnection error...')
           
    def write(self,data):
         self.ser.write(data)
         
    def read(self):
        return self.ser.readline().decode()
    
    def close(self):
        self.ser.close()

    def flush(self):
        self.ser.flush()