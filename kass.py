from time import sleep, time
import sys
import screen
import menu
import settings
import midi_replay
import midi
import led
import greeting
import color_handler
import helper
from gpiozero import Button

screen.init()
if len(sys.argv) != 2 or sys.argv[1] != "skip":
	greeting.greet()

menu.add_sub_menu(color_handler.HandlerSelector)
menu.add_sub_menu(midi_replay.Replay)
menu.add_sub_menu(midi_replay.ReplayViewer)
menu.add_sub_menu(settings.main_settings)
menu.add_sub_menu(midi.MidiStatus)
menu.add_sub_menu(led.LedTest)

menu.init()
led.init()

led_handle = led.LedHandle(is_hsv=True)
led_handle.enable()

_btn = Button(3, hold_time=0.8, bounce_time=0.05)
_btn.when_pressed = sys.exit

_pedal_pos = 0

class LedData:
    def __init__(self):
        self.alpha = 0.0
        self.start_alpha = 0.0
        self.key_down = False
        self.hue = 0.0
        self.sat = 0.0

    def key_press(self, hue, sat, alpha):
        self.alpha = alpha
        self.start_alpha = alpha
        self.hue = hue
        self.sat = sat

led_data_list = [LedData() for _ in range(led.count())]

def midi_handler(msg):
    global _pedal_pos
    if msg.type == "control_change" and msg.control == 64:
        _pedal_pos = msg.value // 60

    if msg.type != "note_on": return
    note_index = msg.note - 21 # Bottom A is note 21

    led_data = led_data_list[note_index]

    vel = msg.velocity / 127.0
    key_down = vel != 0

    led_data.key_down = key_down

    if key_down:
        rescaled_vel = helper.renormalize(vel, 0.3, 0.65, 0, 1)
        
        (hue, sat, val) = color_handler.get_hsv(note_index, rescaled_vel)

        led_data.key_press(hue, sat, vel * val)
        if note_index > 0:
            led_data_list[note_index-1].key_press(hue, sat, vel * val * 0.5)
        if note_index < 87:
            led_data_list[note_index+1].key_press(hue, sat, vel * val * 0.5)

midi.add_callback(midi_handler)

def main():
    while True:
        color_handler.loop()
        midi.loop()

        for i in range(88):
            led_data = led_data_list[i]
            if led_data.alpha == 0:
                led_handle[i] = (led_data.hue, 1, 0)
                continue

            decay_rate_idx = _pedal_pos
            if led_data.key_down:
                decay_rate_idx = 2
            if led_data.alpha > led_data.start_alpha * 0.6:
                decay_rate_idx = 3

            decay_rate = [24, 4, 1, 10][decay_rate_idx]
            led_data.alpha = max(0, led_data.alpha - decay_rate/255.0)

            led_handle[i] = (led_data.hue, led_data.sat, led_data.alpha)
        led_handle.show()

        sleep(0.01)

if __name__ == "__main__":
    try:
        main()
    finally:
        midi.stop()
        led.stop()
        screen.stop()