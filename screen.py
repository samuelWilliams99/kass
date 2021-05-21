# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND
 
#import
import RPi.GPIO as GPIO
import time
import threading
 
# Define GPIO to LCD mapping
_LCD_RS = 6
_LCD_E  = 5
_LCD_D4 = 25
_LCD_D5 = 24
_LCD_D6 = 23
_LCD_D7 = 18
_LCD_BACKLIGHT = 22


_prev_data = ["", ""]
_last_update = time.time()
_idle_time = 35
_awake = True
 
# Define some device constants
_LCD_WIDTH = 16    # Maximum characters per line
_LCD_CHR = True
_LCD_CMD = False
 
_LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
_LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
 
# Timing constants
_E_PULSE = 0.0005
_E_DELAY = 0.0005

def line_width():
    return _LCD_WIDTH

def set_idle_time(t):
    _idle_time = t
 
def init():
    # Main program block
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
    GPIO.setup(_LCD_E, GPIO.OUT)  # E
    GPIO.setup(_LCD_RS, GPIO.OUT) # RS
    GPIO.setup(_LCD_D4, GPIO.OUT) # DB4
    GPIO.setup(_LCD_D5, GPIO.OUT) # DB5
    GPIO.setup(_LCD_D6, GPIO.OUT) # DB6
    GPIO.setup(_LCD_D7, GPIO.OUT) # DB7
    GPIO.setup(_LCD_BACKLIGHT, GPIO.OUT) # backlight

    set_backlight(True)

    # Initialise display
    _byte(0x33,_LCD_CMD) # 110011 Initialise
    _byte(0x32,_LCD_CMD) # 110010 Initialise
    _byte(0x06,_LCD_CMD) # 000110 Cursor move direction
    _byte(0x0C,_LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
    _byte(0x28,_LCD_CMD) # 101000 Data length, number of lines, font size
    _byte(0x01,_LCD_CMD) # 000001 Clear display
    time.sleep(_E_DELAY)

    idle_thread = threading.Thread(target=_idle_check)
    idle_thread.daemon = True
    idle_thread.start()

def add_custom_char(location, data):
    if len(data) != 8 or any(map(lambda row: len(row) != 5, data)):
        raise "Invalid data"

    location *= 8
    location += 64
    _byte(location, _LCD_CMD)

    for row in data:
        row = int(''.join(map(lambda x: '0' if x == ' ' else '1', row)), 2)
        _byte(row, _LCD_CHR)

    _byte(1, _LCD_CMD)

    time.sleep(_E_DELAY)

def stop():
    clear()
    set_backlight(False)
 
def _byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command
 
    GPIO.output(_LCD_RS, mode) # RS
 
    # High bits
    GPIO.output(_LCD_D4, False)
    GPIO.output(_LCD_D5, False)
    GPIO.output(_LCD_D6, False)
    GPIO.output(_LCD_D7, False)
    if bits&0x10==0x10:
        GPIO.output(_LCD_D4, True)
    if bits&0x20==0x20:
        GPIO.output(_LCD_D5, True)
    if bits&0x40==0x40:
        GPIO.output(_LCD_D6, True)
    if bits&0x80==0x80:
        GPIO.output(_LCD_D7, True)
 
    # Toggle 'Enable' pin
    _toggle_enable()
 
    # Low bits
    GPIO.output(_LCD_D4, False)
    GPIO.output(_LCD_D5, False)
    GPIO.output(_LCD_D6, False)
    GPIO.output(_LCD_D7, False)
    if bits&0x01==0x01:
        GPIO.output(_LCD_D4, True)
    if bits&0x02==0x02:
        GPIO.output(_LCD_D5, True)
    if bits&0x04==0x04:
        GPIO.output(_LCD_D6, True)
    if bits&0x08==0x08:
        GPIO.output(_LCD_D7, True)
 
    # Toggle 'Enable' pin
    _toggle_enable()
 
def _toggle_enable():
    # Toggle enable
    time.sleep(_E_DELAY)
    GPIO.output(_LCD_E, True)
    time.sleep(_E_PULSE)
    GPIO.output(_LCD_E, False)
    time.sleep(_E_DELAY)

def clear():
    _byte(0x01, _LCD_CMD)

def line1(message, center=False, typing=False):
    _string(message, _LCD_LINE_1, center, typing)

def line2(message, center=False, typing=False):
    _string(message, _LCD_LINE_2, center, typing)

def wake():
    global _awake
    global _last_update
    c_time = time.time()
    ret_val = False
    if c_time - _last_update > _idle_time:
        set_backlight(True)
        _awake = True
        _stringraw(_prev_data[0], _LCD_LINE_1)
        _stringraw(_prev_data[1], _LCD_LINE_2)
        ret_val = True
    _last_update = c_time
    return ret_val

def is_awake():
    return _awake

def set_backlight(v):
    GPIO.output(_LCD_BACKLIGHT, v)

def _idle_check():
    global _awake
    while True:
        if _awake:
            if time.time() - _last_update > _idle_time:
                _awake = False
                set_backlight(False)
                clear()
            time.sleep(1)
        else:
            clear()
            time.sleep(5)

def _string(message, line, center, typing):
    # Send string to display
    left_spaces = ""
    if center:
        space_count = _LCD_WIDTH - len(message)
        right_space_count = space_count // 2
        left_spaces = ' ' * (space_count - right_space_count)
    
    if typing:
        for i in range(1, len(message) + 1):
            _stringraw(left_spaces + message[:i], line)
            time.sleep(0.05)
    else:
        _stringraw(left_spaces + message, line)

_stringraw_lock = False

def _stringraw(message, line):
    global _stringraw_lock
    while _stringraw_lock:
        time.sleep(_E_PULSE)

    _stringraw_lock = True
    i = 0 if line == _LCD_LINE_1 else 1
    _prev_data[i] = message

    if not _awake: return
    message = message.ljust(_LCD_WIDTH," ")
    _byte(line, _LCD_CMD)
 
    for i in range(_LCD_WIDTH):
        _byte(ord(message[i]),_LCD_CHR)
    _stringraw_lock = False
