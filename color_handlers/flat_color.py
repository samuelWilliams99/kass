import settings
import color_handler

class FlatColor:
    name = "Flat Color"

    @staticmethod
    def loop():
        pass

    @staticmethod
    def get_hsv(note, vel):
        return FlatColor.sub_settings.get_value("Color")

color_handler.add(FlatColor)

FlatColor.add_setting(settings.ColorSetting("Color", (170, 1, 1), is_hsv=True, return_hsv=True))