import settings
import color_handler
import helper

class NoteColor:
    name = "Note Color"

    @staticmethod
    def loop():
        pass

    @staticmethod
    def get_hsv(note, vel):
        hsv_lerp = NoteColor.get_value("Lerp Type")

        start_col = NoteColor.get_value("Start Color", return_hsv=hsv_lerp)
        end_col = NoteColor.get_value("End Color", return_hsv=hsv_lerp)
        increasing = NoteColor.get_value("Increasing")
        loops = NoteColor.get_value("Extra Loops")

        prog = (note / 87.0)

        if hsv_lerp:
            return helper.hsv_lerp(start_col, end_col, prog, increasing, loops)
        else:
            return helper.rgb_to_hsv(helper.rgb_lerp(start_col, end_col, prog))

color_handler.add(NoteColor)

NoteColor.add_setting(settings.ColorSetting("Start Color", (0, 1, 1), is_hsv=True))
NoteColor.add_setting(settings.ColorSetting("End Color", (360, 1, 1), is_hsv=True))
NoteColor.add_setting(settings.BoolSetting("Lerp Type", True, "RGB", "HSV"))
NoteColor.add_setting(settings.BoolSetting("Increasing", True))
NoteColor.add_setting(settings.IntSetting("Extra Loops", 0, 10))