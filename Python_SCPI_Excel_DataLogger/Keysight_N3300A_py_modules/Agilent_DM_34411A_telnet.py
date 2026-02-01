import socket,sys, time

mul_conf = [
    "*RST",
    "CONF:VOLT:DC 20"
]

class Agilent34411A:
    
    def __init__(self,ipAddress="169.254.4.10"):
        try:
            print('trying connection with the multimeter..')
            self.ipAddress=ipAddress
            self.sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sck.connect((self.ipAddress, 5025))
            print("multimeter connected on "+self.ipAddress+" !\n")
            # configurazione del multimetro+
            self.configure(mul_conf)
        except:
            print("failed to connect the multimeter..\n")
            print("\nclosing the program...")
            time.sleep(3)
            sys.exit()

    def format_cmd(self,cmd):
        cmd = "%s\r\n" % cmd
        return cmd.encode()

    def configure(self,conf):
        print("configurating the multimeter..\n")
        for item in conf:
            cmd = self.format_cmd(item)
            #print ("\tcmd=%s" % cmd)
            self.sck.send(cmd)

    def read(self):
        self.sck.send(self.format_cmd('READ?'))
        data = self.sck.recv(1024).decode()
        return data