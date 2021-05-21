from time import time
from random import uniform
import settings
import color_handler

class LedGroup:
    groups = []
    id_counter = 0
    name = "Hue Groups"
    saturation = 1.0
    value = 1.0

    def __init__(self, note, vel):
        self.notes = [note]
        self.update_note_average()
        self.last_note_time = time()
        self.vels = [vel]
        self.id = LedGroup.id_counter
        self.hue = uniform(0, 360) if LedGroup.sub_settings.get_value("Random Hue") else LedGroup.sub_settings.get_value("Fixed Hue")
        LedGroup.id_counter += 1
        LedGroup.groups.append(self)

    def update_note_average(self):
        self.note_average = sum(self.notes) / len(self.notes)

    def try_add(self, note, vel):
        if abs(self.note_average - note) > LedGroup.sub_settings.get_value("Group Range"):
            return
        self.last_note_time = time()
        self.notes.append(note)
        self.vels.append(vel)
        if len(self.vels) > LedGroup.sub_settings.get_value("History Length"):
            self.vels.pop(0)
            self.notes.pop(0)
        self.update_note_average()

        return sum(self.vels) / len(self.vels)

    def remove_check(self):
        if time() - self.last_note_time > LedGroup.sub_settings.get_value("Group Timeout"):
            LedGroup.groups.remove(self)

    @staticmethod
    def loop():
        for group in LedGroup.groups:
            group.remove_check()

    @staticmethod
    def get_hsv(note, input_value):
        group = min(LedGroup.groups, key=lambda group: abs(group.note_average - note), default=None)
        if group:
            value = group.try_add(note, input_value)
            if value:
                return (LedGroup.calc_hue(value, group.hue), LedGroup.saturation, LedGroup.value)

        new_group = LedGroup(note, input_value)
        
        return (LedGroup.calc_hue(input_value, new_group.hue), LedGroup.saturation, LedGroup.value)

    @staticmethod
    def calc_hue(vel, hue):
        if LedGroup.sub_settings.get_value("Show Velocity"):
            return (hue + (vel * 120)) % 360
        else:
            return hue

color_handler.add(LedGroup)

LedGroup.add_setting(settings.IntSetting("Group Range", 24, 48))
LedGroup.add_setting(settings.IntSetting("History Length", 10, 20))
LedGroup.add_setting(settings.NumberSetting("Group Timeout", 2.0, 10.0, 0.1))
LedGroup.add_setting(settings.BoolSetting("Random Hue", True))
LedGroup.add_setting(settings.IntSetting("Fixed Hue", 0, 360))
LedGroup.add_setting(settings.BoolSetting("Show Velocity", True))