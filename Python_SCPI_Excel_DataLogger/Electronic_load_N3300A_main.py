from Keysight_N3300A_py_modules import *
import keyboard

#----------------------------------------------------------------------
    #START CONNECTION
#----------------------------------------------------------------------

print('-----------------------------------------------------------------------------------')
print("Electronic load N3300A software - version 1.5 - August 2023")
print("by Molari Stefano")
print('-----------------------------------------------------------------------------------')

print("\ntrying to connect to the electronic load and the stm32..\n")

cmd = ELN3300ACommands()

ser_eload = ELN3300ASerial("COM6",9600)
ser_stm = Stm32_serial("COM5",115200)
mult = Agilent34411A("169.254.4.10")
log = Excel_data_logger()



#----------------------------------------------------------------------------
    #FUNCTIONS
#----------------------------------------------------------------------------
def manual_commands(): 
    print('------------------------------------------------------------------------------------')
    print('Send manual commands to the eload')
    print('------------------------------------------------------------------------------------')
    print("\nenter \"MENU\" to go back")
    goOn=True
    while(goOn):   #loop to send commands manually
        command=input("enter the command:")
        #print("you entered:"+command)  #debug
        if(command=="MENU"):
            goOn=False
            break
        print("sending..(timeout:5s)\n")
        ser_eload.write(cmd.f_cmd(command))
        if("?" in command):
            response=ser_eload.read()
            print('response:'+ response )
#----------------------------------------------------------------------------
def ask_test_current():
    max_current = 16
    current=0
    while((current>=max_current)or(current==0)):
        #try:
        current = float(input(str('Set the CC value('+str(max_current)+'[A] max, 0 not allowed):\n'))) 
        #except ValueError:
            #print('Enter a valid number')
        if((current>=max_current)or(current==0)):
            print("invalid value\n")
    print("current:",current)
    return current

def CC_mode_logger():
    #------------------------------------------------------------------------------------    
        #ELOAD CONFIGURATION
    #------------------------------------------------------------------------------------    
    print('-----------------------------------------------------------------------------------')
    print("CC mode with data logging")
    print('-----------------------------------------------------------------------------------')
    current = ask_test_current()
    cmd.initialize_CC(ser_eload,current)

    #------------------------------------------------------------------------------------    
        #MEASURE AND LOG TENSION AND CURRENT
    #------------------------------------------------------------------------------------    
    print("\nlogging data..")
    ser_eload.write(cmd.input_on())   #turn on the input at the maximum slew rate
       
    goOnLogging=True
    meas_index=0
    ser_eload.ser.reset_input_buffer()
    ser_stm.ser.reset_input_buffer()
    
    while(goOnLogging):
        ser_eload.write(cmd.singleMeasure_i()) #read istant current from the load
        curr=ser_eload.read()
        #print('current:'+ curr )

        ser_eload.write(cmd.singleMeasure_v()) #read istant tension from the load
        tens=ser_eload.read()
        #print('tension:'+ tens )
        stm_data=ser_stm.read().split(",")
        log.storeDataELN3300A(cmd.df_cmd(curr),cmd.df_cmd(tens),stm_data[0],stm_data[1],meas_index)
        meas_index=meas_index+1
        if keyboard.is_pressed('ù'):  # if key 's' is pressed 
            goOnLogging=False
            ser_eload.write(cmd.reset())
            ser_eload.write(cmd.cls())
            ser_eload.write(cmd.input_off())
            print("\ntest done.")
            log.save()
            time.sleep(0.5)
#----------------------------------------------------------------------------
def stm_logger():
    print('-----------------------------------------------------------------------------------')
    print('\t\tstm32 Nucleo data logging')
    print('-----------------------------------------------------------------------------------')
    goOnLogging=True
    meas_index=0
    ser_eload.ser.reset_input_buffer()
    ser_stm.ser.reset_input_buffer()
    
    while(goOnLogging):
        stm_data=ser_stm.read().split(",")
        log.storeDataSTM32(stm_data[0],stm_data[1],meas_index)
        meas_index=meas_index+1
        if keyboard.is_pressed('s'):  # if key 's' is pressed 
            goOnLogging=False
            print("\ntest done.")
            log.save()
            time.sleep(0.5) 

def stm_DM_logger():
    print('-----------------------------------------------------------------------------------')
    print('\t\tstm32 Nucleo + Agilent + data logging')
    print('-----------------------------------------------------------------------------------')
    goOnLogging=True
    meas_index=0
    ser_stm.ser.reset_input_buffer()
    

    while(goOnLogging):
        stm_data=ser_stm.read().split(",")
        mult_tens=mult.read()
        log.storeDataSTM32DM(stm_data[0],stm_data[1],mult_tens,meas_index)
        meas_index=meas_index+1
        if keyboard.is_pressed('ù'):  # if key 's' is pressed 
            goOnLogging=False
            print("\ntest done.")
            log.save()
            time.sleep(0.5) 
#----------------------------------------------------------------------------
def load_mult_stm_logger():
    print('-----------------------------------------------------------------------------------')
    print('\teload N3300A + stm32 Nucleo + mult Agilent34411A')
    print('-----------------------------------------------------------------------------------')

    #------------------------------------------------------------------------------------    
        #ELOAD CONFIGURATION
    #------------------------------------------------------------------------------------    
    print('-----------------------------------------------------------------------------------')
    print("CC mode with data logging")
    print('-----------------------------------------------------------------------------------')
    current = ask_test_current()
    cmd.initialize_CC(ser_eload,current)

    #------------------------------------------------------------------------------------    
        #MEASURE AND LOG TENSION AND CURRENT
    #------------------------------------------------------------------------------------    
    print("\nlogging data..")
    ser_eload.write(cmd.input_on())   #turn on the input at the maximum slew rate
       
    goOnLogging=True
    meas_index=0
    ser_eload.ser.reset_input_buffer()
    ser_stm.ser.reset_input_buffer()
    
    while(goOnLogging):
        ser_eload.write(cmd.singleMeasure_i()) #read istant current from the load
        curr=ser_eload.read()
        #print('current:'+ curr )

        ser_eload.write(cmd.singleMeasure_v()) #read istant tension from the load
        tens=ser_eload.read()
        #print('tension:'+ tens )

        mult_tens= mult.read() #read the battery tension using the multimeter

        stm_data=ser_stm.read().split(",")

        log.storeDataELN3300A_DM_STM32(cmd.df_cmd(curr),cmd.df_cmd(tens),mult_tens,stm_data[0],stm_data[1],meas_index)
        meas_index=meas_index+1

        if keyboard.is_pressed('ù'):  # if key 's' is pressed 
            goOnLogging=False
            ser_eload.write(cmd.reset())
            ser_eload.write(cmd.cls())
            ser_eload.write(cmd.input_off())
            print("\ntest done.")
            log.save()
            time.sleep(0.5)
#-----------------------------------
#----------------------------------------------------------------------
    #MENU
#----------------------------------------------------------------------------
    #1 send commands manually
    #2 CC mode with data logging on Excel
    #3 stm32 data logging
    #q exit and close the program
ser_stm.checkPortOpen()
ser_eload.checkPortOpen(cmd)
goOn1=True
while(goOn1):
    print('-----------------------------------------------------------------------------------')
    print("MENU")
    print('-----------------------------------------------------------------------------------')
    inp1=input("-press \"1\" to send commands manually to the eLoad\n"
          "-press \"2\" to use: eLoad (CC mode) + stm32 + EXCEL logger\n"
          "-press \"3\" to use: eLoad (CC mode) + stm32 + DM + EXCEL logger\n"
          "-press \"4\" to use: stm32 + Excel logger\n"
          "-press \"5\" to use: stm32 + DM +Excel logger\n"
          "-press \"q\" to exit and close the program\n")
    if(inp1=="1"):
        manual_commands()
    elif(inp1=="2"):
        CC_mode_logger()  
    elif(inp1=="3"):
        load_mult_stm_logger()    
    elif(inp1=="4"):
        stm_logger()  
    elif(inp1=="5"):
        stm_DM_logger()       
    elif(inp1=="q"):
        goOn1=False
    else:
        print("\nERROR\ninsert a valid input!\n")

print("\nclosing the program...")
ser_eload.close()
ser_stm.close()  
time.sleep(3)
