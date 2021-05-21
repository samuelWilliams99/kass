import menu
import screen
import math
import settings
import json

_handler_save_path = "/home/pi/python/handler_data.txt"

class HandlerSelector:
    name = "COLOR TYPE"
    handlers = []
    force_next_setting = False
    handler_data = {"index": 0}

    @staticmethod
    def get_select_text():
        return HandlerSelector.get_handler().name

    @staticmethod
    def add(handler):
        handler.sub_settings = ColorHandlerSettingHandler(handler.name, "")
        handler.add_setting = lambda setting: handler.sub_settings.add(setting)
        HandlerSelector.handlers.append(handler)

    @staticmethod
    def on_button_pressed():
        menu.leave_sub_menu()

    @staticmethod
    def on_button_long_pressed():
        handler = HandlerSelector.get_handler()
        if len(handler.sub_settings.setting_names) > 0:
            menu.set_temp_sub_menu(handler.sub_settings)

    @staticmethod
    def on_enter():
        HandlerSelector.force_next_setting = True

    @staticmethod
    def on_value_change(v):
        handler_count = len(HandlerSelector.handlers)
        new_index = min(math.floor(v * handler_count), handler_count - 1)
        if HandlerSelector.handler_index() != new_index or HandlerSelector.force_next_setting:
            HandlerSelector.force_next_setting = False
            HandlerSelector.set_handler_index(new_index)

    @staticmethod
    def handler_index():
        return HandlerSelector.handler_data["index"]

    @staticmethod
    def set_handler_index(i):
        HandlerSelector.handler_data["index"] = i
        HandlerSelector.update_display()
        HandlerSelector.save()

    @staticmethod
    def update_display():
        screen.line1("[" + HandlerSelector.name + "]", True)
        screen.line2(HandlerSelector.get_handler().name, True)

    @staticmethod
    def get_handler():
        return HandlerSelector.handlers[HandlerSelector.handler_index()]

    @staticmethod
    def get_hsv(note, vel):
        return HandlerSelector.get_handler().get_hsv(note, vel)

    @staticmethod
    def loop():
        return HandlerSelector.get_handler().loop()

    @staticmethod
    def save():
        with open(_handler_save_path, 'w') as f:
            json.dump(HandlerSelector.handler_data, f)

    @staticmethod
    def save_settings(name, data):
        HandlerSelector.handler_data[name] = data
        HandlerSelector.save()

try:
    with open(_handler_save_path, 'r') as f:
        HandlerSelector.handler_data = json.load(f)
except:
    pass

class ColorHandlerSettingHandler(settings.SettingHandler):
    def save_json(self, data):
        HandlerSelector.save_settings(self.name, data)

    def load_json(self):
        return HandlerSelector.handler_data.get(self.name, dict())


def add(handler):
    HandlerSelector.add(handler)

def loop():
    HandlerSelector.loop()

def get_hsv(note_index, vel):
    return HandlerSelector.get_hsv(note_index, vel)

import color_handlers