import screen
import menu
import json
import math
import led
import os
from time import sleep
from sys import exit

_save_file_path = "/home/pi/python/midi_lights_save.txt"

class SettingHandler:
    def __init__(self, name, path):
        self.settings = dict()
        self.setting_names = []
        self.setting_index = 0
        self.name = name
        self.force_next_setting = False
        self.save_path = path

        self.default_data = self.load_json()

    def clear_settings(self):
        self.settings = dict()
        self.setting_names = []

    def set_setting_index(self, idx):
        self.setting_index = idx
        self.update_display()

    def update_display(self):
        setting = self.get_current()
        setting.update_display()

    def add(self, setting):
        self.setting_names.append(setting.name)
        self.settings[setting.name] = setting
        setting.set_handler(self)
        return setting

    def on_value_change(self, v):
        setting_count = len(self.setting_names)
        new_index = min(math.floor(v * setting_count), setting_count - 1)
        if self.setting_index != new_index or self.force_next_setting:
            self.force_next_setting = False
            self.set_setting_index(new_index)

    def on_enter(self):
        self.force_next_setting = True
        self.save()

    def on_button_pressed(self):
        setting = self.get_current()
        if setting.is_menu:
            menu.set_temp_sub_menu(setting)
        else:
            setting.on_trigger()
            self.update_display()
            self.save()

    def on_button_long_pressed(self):
        menu.leave_sub_menu()

    def get_value(self, name):
        setting = self.settings.get(name)
        if setting == None: return
        return setting.get_use_value()

    def get_current(self):
        return self.settings[self.setting_names[self.setting_index]]

    def save(self):
        data = dict()
        for name, setting in self.settings.items():
            if not setting.should_save: continue
            data[name] = setting.get_save_value()

        self.save_json(data)

    def save_json(self, data):
        with open(self.save_path, 'w') as f:
            json.dump(data, f)

    def load_json(self):
        try:
            with open(self.save_path, 'r') as f:
                return json.load(f)
        except:
            return dict()


class Setting:
    value = None
    should_save = False
    is_menu = True

    def __init__(self, name):
        self.name = name
        self.change_callback = None
        self.handler = None

    def on_button_pressed(self):
        menu.leave_sub_menu()

    def set_handler(self, handler):
        self.handler = handler
        def_val = handler.default_data.get(self.name)
        if def_val is not None:
            self.value = def_val

    def set_change_callback(self, f):
        self.change_callback = f
        self.change_callback(self.value)

    def get_display_data(self):
        return "NO TYPE"

    def get_display_data_full(self):
        data = self.get_display_data()
        if type(data).__name__ == "tuple":
            return data
        else:
            return data, True

    def update_display(self, editing=False):
        name = self.name
        if editing: name = "[" + name + "]"
        screen.line1(name, True)
        text, center = self.get_display_data_full()
        screen.line2(text, center)

    def get_save_value(self):
        return self.value

    def get_use_value(self):
        return self.value

class NumberSetting(Setting):
    def __init__(self, name, value, max_value=100, min_step=0.01):
        self.value = value
        self.max_value = max_value
        self.should_save = True
        self.min_step = min_step
        super(NumberSetting, self).__init__(name)

    def get_display_data(self):
        prog = self.value / float(self.max_value)

        bars = int(round(prog * 10))

        return '<' + ('\xff' * bars) + (' ' * (10 - bars)) + '>'

    def on_value_change(self, val):
        self.value = round((self.max_value * val) / self.min_step) * self.min_step
        if self.change_callback: self.change_callback(self.value)
        self.update_display(True)

class IntSetting(NumberSetting):
    def __init__(self, name, value, max_value=100):
        super(IntSetting, self).__init__(name, value, max_value, 1)

class TimeSetting(NumberSetting):
    def __init__(self, name, value, max_value=100):
        super(TimeSetting, self).__init__(name, value, max_value, 10)

    def get_display_data(self):
        m, s = divmod(self.value, 60)
        return f'{m:02d}:{s:02d}'

class NoteSetting(Setting):
    @staticmethod
    def midi_callback(msg):
        if msg.type != "note_on": return
        setting = NoteSetting.active_setting
        if setting:
            setting.value = msg.note - 21
            if setting.change_callback: setting.change_callback(setting.value)
            menu.leave_sub_menu()

    def __init__(self, name, value):
        self.value = value
        self.should_save = True
        NoteSetting.active_setting = None
        super(NoteSetting, self).__init__(name)

    def on_enter(self):
        NoteSetting.active_setting = self
        self.update_display()

    def on_leave(self):
        NoteSetting.active_setting = None

    def get_display_data(self):
        if NoteSetting.active_setting:
            return "Press Note"
        else:
            return str(self.value)

class BoolSetting(Setting):
    def __init__(self, name, value, off_message="FALSE", on_message="TRUE"):
        self.value = value
        self.should_save = True
        self.is_menu = False
        self.on_message = on_message
        self.off_message = off_message
        super(BoolSetting, self).__init__(name)

    def get_display_data(self):
        return self.on_message if self.value else self.off_message

    def on_trigger(self):
        self.value = not self.value
        if self.change_callback: self.change_callback(self.value)

class ActionSetting(Setting):
    def __init__(self, name, callback, message="PRESS BUTTON", complete_message=None):
        self.callback = callback
        self.pending_message = message
        self.complete_message = complete_message
        self.show_complete = False
        self.is_menu = False
        super(ActionSetting, self).__init__(name)

    def get_display_data(self):
        message = self.pending_message
        if self.show_complete:
            self.show_complete = False
            message = self.complete_message
        return message

    def on_trigger(self):
        self.callback()
        if self.complete_message:
            self.show_complete = True

class SpecialActionSetting(Setting):
    def __init__(self, name, callback, message="PRESS BUTTON", complete_message=None):
        self.callback = callback
        self.pending_message = message
        self.complete_message = complete_message
        self.message_mode = 0 # 0 -> pending, 1 -> confirm, 2 -> complete
        super(SpecialActionSetting, self).__init__(name)

    def get_display_data(self):
        if self.message_mode == 0:
            return self.pending_message
        elif self.message_mode == 1:
            return "LONG PRESS"
        else:
            self.message_mode = 0
            return self.complete_message

    def on_enter(self):
        self.message_mode = 1
        self.update_display(True)

    def on_leave(self):
        if self.message_mode == 1:
            self.message_mode = 0

    def on_button_long_pressed(self):
        self.callback()
        if self.complete_message:
            self.message_mode = 2
        else:
            self.message_mode = 0
        menu.leave_sub_menu()

class ColorSetting(SettingHandler, Setting):
    led_handle = led.LedHandle(False, True)
    def __init__(self, name, value, is_hsv=False, allow_hsv_change=True, return_hsv=False):
        self.value = value
        self.is_hsv = is_hsv
        self.should_save = True
        self.active = False
        self.allow_hsv_change = allow_hsv_change
        self.return_hsv = return_hsv

        SettingHandler.__init__(self, name, "")

    def update_display(self):
        if self.active:
            SettingHandler.update_display(self)
        else:
            Setting.update_display(self)

    def get_display_data(self):
        v = self.value
        val = "(" + str(round(v[0])) + "," + str(round(v[1], 2)) + "," + str(round(v[2], 2)) + ")"
        return ("H" if self.is_hsv else "R") + val

    def get_save_value(self):
        return (self.value, self.is_hsv)

    def get_use_value(self):
        if self.is_hsv and not self.return_hsv:
            return led.hsv_to_rgb(self.value)
        if not self.is_hsv and self.return_hsv:
            return led.rgb_to_hsv(self.value)
        return self.value

    def add_value_setting(self, i, setting):
        def setter(v):
            value = list(self.value)
            value[i] = v
            self.value = tuple(value)
            self.update_leds()
        self.add(setting).set_change_callback(setter)

    def on_button_long_pressed(self):
        ColorSetting.led_handle.disable()
        self.active = False
        menu.leave_sub_menu()

    def on_enter(self):
        self.active = True
        self.force_next_setting = True
        ColorSetting.led_handle.enable()
        self.update_leds()

    def update_leds(self):
        value = self.value
        if self.is_hsv:
            value = led.hsv_to_rgb(self.value)
        ColorSetting.led_handle.fill(value, 3)
        ColorSetting.led_handle.show()

    def setup_settings(self):
        self.clear_settings()
        if self.is_hsv:
            self.add_value_setting(0, IntSetting("Hue", self.value[0], 360))
            self.add_value_setting(1, NumberSetting("Saturation", self.value[1], 1))
            self.add_value_setting(2, NumberSetting("Value", self.value[2], 1))
        else:
            self.add_value_setting(0, IntSetting("Red", self.value[0], 255))
            self.add_value_setting(1, IntSetting("Green", self.value[1], 255))
            self.add_value_setting(2, IntSetting("Blue", self.value[2], 255))
        if self.allow_hsv_change:
            self.add(BoolSetting("Color Type", self.is_hsv, "RGB", "HSV")).set_change_callback(self.on_hsv_change)

    def on_hsv_change(self, new_hsv):
        if new_hsv == self.is_hsv: return
        self.is_hsv = new_hsv
        if self.is_hsv:
            (h, s, v) = led.rgb_to_hsv(self.value)
            self.value = (int(h), s, v)
        else:
            self.value = tuple(map(int, led.hsv_to_rgb(self.value)))

        self.setup_settings()

    def save(self):
        pass
        
    def load_json(self):
        return dict()

    def set_handler(self, handler):
        self.handler = handler
        def_val = handler.default_data.get(self.name)
        if def_val is not None:
            self.value = def_val[0]
            self.is_hsv = def_val[1]
        self.setup_settings()

main_settings = SettingHandler("Settings", _save_file_path)

def get_value(name):
    return main_settings.get_value(name)

def shutdown():
    screen.clear()
    screen.line1("Goodbye!", True)
    sleep(1)
    screen.stop()
    os.system("sudo poweroff")
    exit()

def add(setting):
    main_settings.add(setting)
    return setting

add(SpecialActionSetting("Shutdown", shutdown))
