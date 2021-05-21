import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
import threading
from time import sleep
from adafruit_mcp3xxx.analog_in import AnalogIn
 
# create the spi bus
_spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
 
# create the cs (chip select)
_cs = digitalio.DigitalInOut(board.D27)
 
# create the mcp object
_mcp = MCP.MCP3008(_spi, _cs)
 
# create an analog input channel on pin 0
_chan0 = AnalogIn(_mcp, MCP.P0)

_last_read = -1000  # this keeps track of the last potentiometer value
_tolerance = 250    # to keep from being jittery we'll only change
                    # volume when the pot has moved a significant amount
                    # on a 16-bit ADC

_callback = lambda x: None

def set_callback(f):
    global _callback
    _callback = f

def _analog_check():
    global _last_read
    while True:
        # we'll assume that the pot didn't move
        trim_pot_changed = False
     
        # read the analog pin
        trim_pot = _chan0.value
     
        # how much has it changed since the last read?
        pot_adjust = abs(trim_pot - _last_read)
     
        if pot_adjust > _tolerance:
            trim_pot_changed = True
     
        if trim_pot_changed:
            value = trim_pot / 65535.0
            
            _callback(value)
                 
            # save the potentiometer reading for the next loop
            _last_read = trim_pot
     
        # hang out and do nothing for a half second
        sleep(0.1)

def init():
    analog_thread = threading.Thread(target=_analog_check)
    analog_thread.daemon = True
    analog_thread.start()