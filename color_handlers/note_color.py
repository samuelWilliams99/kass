import settings
import color_handler

class NoteColor:
    name = "Note Color"

    @staticmethod
    def loop():
        pass

    @staticmethod
    def get_hsv(note, vel):
        (start_hue, start_sat, start_val) = NoteColor.sub_settings.get_value("Start Color")
        (end_hue, end_sat, end_val) = NoteColor.sub_settings.get_value("End Color")
        increasing = NoteColor.sub_settings.get_value("Increasing")
        loops = NoteColor.sub_settings.get_value("Extra Loops")

        if increasing and end_hue < start_hue: end_hue += 360
        if not increasing and start_hue < end_hue: start_hue += 360

        end_hue += (1 if increasing else -1) * loops * 360

        prog = (note / 87.0)
        hue = (start_hue + prog * (end_hue - start_hue)) % 360
        sat = (start_sat + prog * (end_sat - start_sat))
        val = (start_val + prog * (end_val - start_val))

        return (hue, sat, val)

color_handler.add(NoteColor)

NoteColor.add_setting(settings.ColorSetting("Start Color", (0, 1, 1), is_hsv=True, return_hsv=True))
NoteColor.add_setting(settings.ColorSetting("End Color", (360, 1, 1), is_hsv=True, return_hsv=True))
NoteColor.add_setting(settings.BoolSetting("Increasing", True))
NoteColor.add_setting(settings.IntSetting("Extra Loops", 0, 10))