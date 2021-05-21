import mido
import menu
import screen
import threading
import settings
import led
from time import sleep

_input_port = None
_output_port = None
_midi_event_callbacks = []
_midi_status_active = False

settings.add(settings.BoolSetting("Lights on Send", True))

class MidiStatus():
    name = "MIDI STATUS"

    @staticmethod
    def on_button_pressed():
        menu.leave_sub_menu()

    @staticmethod
    def on_button_long_pressed():
        menu.leave_sub_menu()

    @staticmethod
    def on_enter():
        global _midi_status_active
        _midi_status_active = True
        screen.line1("MIDI STATUS", True)
        screen.line2("Checking...", True)

    @staticmethod
    def on_leave():
        global _midi_status_active
        _midi_status_active = False

    @staticmethod
    def init():
        midi_thread = threading.Thread(target=port_handler)
        midi_thread.daemon = True
        midi_thread.start()

def port_handler():
    global _input_port
    global _output_port
    port_message = ""
    while True:
        input_port_names = mido.get_input_names()
        if _input_port and _input_port.name not in input_port_names: _input_port = None

        if _input_port == None:
            input_port_name = None
            for port in input_port_names:
                if "Grand" in port:
                    input_port_name = port
                    break

            if input_port_name == None:
                port_message = "NO GRAND PIANO"
                on_disconnect()
            else:
                try:
                    _input_port = mido.open_input(input_port_name)
                    _output_port = mido.open_output(input_port_name)
                    port_message = "CONNECTED"
                    on_connect()
                except:
                    port_message = "PORT ERROR"
                    on_disconnect()
        if _midi_status_active:
            screen.line2(port_message, True)
        sleep(1)

_connected = False

def on_connect():
    global _connected
    if _connected: return
    _connected = True
    led.pulse((0, 10, 0))

def on_disconnect():
    global _connected
    if not _connected: return
    _connected = False
    led.pulse((10, 0, 0))

def stop():
    if _input_port:
        _input_port.close()
    if _output_port:
        _output_port.close()

def send(msg):
    global _output_port
    if _output_port == None:
        return

    if _output_port.closed or _output_port.name not in mido.get_output_names():
        _output_port = None
        on_disconnect()
        return

    if settings.get_value("Lights on Send"):
        trigger_callbacks(msg)
    _output_port.send(msg)

def loop():
    global _input_port
    if _input_port == None:
        return

    if _input_port.closed or _input_port.name not in mido.get_input_names():
        _input_port = None
        on_disconnect()
        return

    for msg in _input_port.iter_pending():
        trigger_callbacks(msg)

def trigger_callbacks(msg):
    for f in _midi_event_callbacks:
        f(msg)

def add_callback(f):
    _midi_event_callbacks.append(f)

add_callback(settings.NoteSetting.midi_callback)
