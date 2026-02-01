import time

class  ELN3300ACommands:
    #attributes
    
    #methods
    def f_cmd(self,cmd):
        cmd = "%s\n" %cmd#see "programming guide" - pag 19-20
        return cmd.encode()
    
    def df_cmd(self,command):
        return str(command).strip()
    
    def ask_cmd(self):
        command=input("enter the command:")
        return str(command)
    
    def initialize_CC(self,ser,current):
        #COSTANT CURRENT MODE (CC)
        #pag22 user manual
        print("\nconfigurating the instrument..\nCC mode")
        ser.write(self.reset())                  #reset the device PG-pag102
        ser.write(self.cls())                    #clear regosters  PG-pag99
        ser.write(self.currentMode())            #set the mode
        ser.write(self.setCurrentRange("MAX"))   #set the current range
        ser.write(self.setTensionRange("MAX"))   #set the tension range
        ser.write(self.setCurrent(current))            #set the current [A]
        time.sleep(2)
        print("DONE!")

    def deviceInfo(self):#metodo
        return self.f_cmd("*IDN?")
    
    def reset(self):#metodo
        return self.f_cmd("*RST")

    def cls(self):
        return self.f_cmd("*CLS")

    def singleMeasure_v(self):
        return self.f_cmd("MEAS:VOLT?")
    
    def singleMeasure_i(self):
        return self.f_cmd("MEAS:CURR?")

    def current_max(self):
        return self.f_cmd("MEAS:CURR?")
    
    #When off, the electronic load input is disabled and the Dis annunciator is on.
    def input_on(self):
        print("\nELOAD INPUT ON!!\n") 
        return self.f_cmd("INP ON")
    
    def input_off(self):
        print("\nELOAD INPUT OFF!!\n") 
        return self.f_cmd("INP OFF")
    
    def setCurrentRange(self,range):
        return self.f_cmd("SENS:CURR:RANG "+range)
    
    def setTensionRange(self,range):
        return self.f_cmd("SENS:VOLT:RANG "+range)
    
    def setCurrent(self,curr):
        return self.f_cmd("CURR "+str(curr))
    
    def setTension(self,tens):
        return self.f_cmd("VOLT "+str(tens))
    
    def currentMode(self):
        return self.f_cmd("CURR:MODE FIX")
    
    def currentProtection(self,max):
        return self.f_cmd("CURR:PROT "+str(max))
    