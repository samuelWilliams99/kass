import led
import threading

_octave_size = 12
_octave_max_delay = 0.05

last_octave_notes = None
last_octave_notes_preempt = None

def _check_direction(note, dir, led_data):
    time_down = led_data[note].time_down

    last_note = note + (dir * _octave_size)
    if last_note < 0 or last_note > 87: return
    last_led = led_data[last_note]

    if not (last_led.key_down and time_down - last_led.time_down < _octave_max_delay): return
    for i in range(note + dir, last_note, dir):
        if led_data[i].key_down: return

    if note > last_note: return last_note, note
    else: return note, last_note

def key_press(note, vel, led_data):
    global last_octave_notes_preempt
    note_data = _check_direction(note, -1, led_data) or _check_direction(note, 1, led_data)
    if not note_data: return

    last_octave_notes_preempt = note_data
    thread = threading.Timer(_octave_max_delay, key_press_delayed, args=[note_data[0], note_data[1], vel, led_data])
    thread.daemon = True
    thread.start()

def key_press_delayed(low_note, high_note, vel, led_data):
    global last_octave_notes
    for i in range(low_note + 1, high_note):
        if led_data[i].key_down: return
    last_octave_notes = (low_note, high_note)