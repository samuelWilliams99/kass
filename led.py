import neopixel
import board
import threading
import menu
import screen
import settings
import math
import helper
from time import sleep

_NUM_LEDS = 88
_leds = None

class LedHandle:
    overriding_handle = None
    finished = False
    reversed = False

    @staticmethod
    def set_reversed(v):
        LedHandle.reversed = v

    @staticmethod
    def get_real_idx(i):
        if LedHandle.reversed:
            return _NUM_LEDS - 1 - i
        return i

    def __init__(self, is_hsv=False, is_overrider=False):
        self.enabled = False
        self.is_overrider = is_overrider
        self.is_hsv = is_hsv

    def set_hsv(self, v):
        self.is_hsv = v

    def enable(self):
        if self.enabled: return
        if self.is_overrider:
            if LedHandle.overriding_handle:
                return False
            else:
                LedHandle.overriding_handle = self

        self.enabled = True

        if self.is_overrider:
            self.clear()
            self.show()
        return True

    def disable(self):
        if not self.enabled: return
        if self.is_overrider:
            if self.is_overrider:
                self.clear()
                self.show()
            LedHandle.overriding_handle = None
        self.enabled = False

    def set_overriding(self, v):
        if v == self.is_overrider: return
        if self.enabled:
            raise Exception("Cannot change mode while enabled")
        self.is_overrider = v

    def to_rgb(self, col):
        if self.is_hsv:
            return helper.hsv_to_rgb(col)
        return col

    def can_assign(self):
        if not self.enabled: return False
        if not self.is_overrider and LedHandle.overriding_handle: return False
        if LedHandle.finished: return False
        return True

    def fill(self, col, every=1):
        if not self.can_assign(): return

        col = self.to_rgb(col)
        if every == 1:
            _leds.fill(col)
        else:
            for i in range(0, _NUM_LEDS, every):
                _leds[LedHandle.get_real_idx(i)] = col

    def pulse(self, col, cb=None):
        col = self.to_rgb(col)
        thread = threading.Thread(target=self._pulse, args=[col, cb])
        thread.daemon = True
        thread.start()

    def _pulse(self, col, cb):
        prog = 0
        while prog <= 1:
            prog = round(prog + 0.05, 2)
            sine_prog = math.sin(math.pi * min(prog, 1))
            _col = (col[0] * sine_prog, col[1] * sine_prog, col[2] * sine_prog)
            if self.can_assign():
                _leds.fill(_col)
                _leds.show()
            sleep(0.01)
        if cb:
            cb()

    def __setitem__(self, i, col):
        if not self.can_assign(): return

        _leds[LedHandle.get_real_idx(i)] = self.to_rgb(col)

    def show(self):
        if not self.can_assign(): return

        _leds.show()

    def clear(self):
        if not self.can_assign(): return

        _leds.fill((0,0,0))

class LedTest:
    name = "LED Test"
    thread = None
    running = False
    handle = LedHandle(True, True)

    @staticmethod
    def on_button_pressed():
        menu.leave_sub_menu()

    @staticmethod
    def on_button_long_pressed():
        menu.leave_sub_menu()

    @staticmethod
    def on_enter():
        screen.line2("Press to stop", True)
        LedTest.handle.enable()
        LedTest.running = True
        LedTest.thread = threading.Thread(target=LedTest.run)
        LedTest.thread.daemon = True
        LedTest.thread.start()

    @staticmethod
    def on_leave():
        LedTest.running = False
        LedTest.handle.disable()

    @staticmethod
    def run():
        hue = 0
        while LedTest.running:
            LedTest.handle.fill((hue, 1, 0.3), 3)
            LedTest.handle.show()
            hue = (hue + 1) % 360
            sleep(0.1)

pulse_handle = LedHandle(is_overrider=True)

def pulse(col):
    if pulse_handle.enable():
        pulse_handle.pulse(col, lambda: pulse_handle.disable())

def init():
    global _leds
    _leds = neopixel.NeoPixel(board.D21, _NUM_LEDS, auto_write=False)

    settings.add(settings.BoolSetting("Reverse LEDs", False)).set_change_callback(LedHandle.set_reversed)

def stop():
    LedHandle.finished = True
    _leds.fill((0, 0, 0))
    _leds.show()

def count():
    return _NUM_LEDS