#pip install pyvisa-py numpy matplotlib
import pyvisa
rm = pyvisa.ResourceManager()
print(rm.list_resources())
