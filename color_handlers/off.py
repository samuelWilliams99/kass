import color_handler

class ColorOff:
    name = "Off"

    @staticmethod
    def loop():
        pass

    @staticmethod
    def get_hsv(note, vel):
        return (0, 0, 0)

color_handler.add(ColorOff)