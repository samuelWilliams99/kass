from time import time
import settings
import color_handler
import helper

class AdaptiveColor:
    name = "Adaptive"
    vels = None
    delays = None
    vel_avg = None
    delay_avg = None
    last_time = None
    min_time = 0.05
    max_delay = 0.5
    min_delay = 0.05
    global_hue = True

    clear_time = 1

    @staticmethod
    def clear_history(_):
        AdaptiveColor.last_time = None

    @staticmethod
    def loop():
        pass

    @staticmethod
    def get_hsv(note, vel):
        hsv_lerp = AdaptiveColor.get_value("Lerp Type")
        use_vel = AdaptiveColor.get_value("Use Velocity")
        use_speed = AdaptiveColor.get_value("Use Play Speed")
        start_col = AdaptiveColor.get_value("Start Color", return_hsv=hsv_lerp)
        end_col = AdaptiveColor.get_value("End Color", return_hsv=hsv_lerp)
        history_size = AdaptiveColor.get_value("History")
        delays_weight = AdaptiveColor.get_value("Speed Weight")
        AdaptiveColor.global_hue = AdaptiveColor.get_value("Global Hue")

        c_time = time()

        if AdaptiveColor.last_time == None:
            AdaptiveColor.last_time = c_time - AdaptiveColor.clear_time

        delay = c_time - AdaptiveColor.last_time

        if delay >= AdaptiveColor.clear_time:
            AdaptiveColor.delays = [AdaptiveColor.max_delay] * history_size
            AdaptiveColor.delay_avg = AdaptiveColor.max_delay
            AdaptiveColor.vels = [vel] * history_size
            AdaptiveColor.vel_avg = vel

        if delay > AdaptiveColor.min_time:
            AdaptiveColor.last_time = c_time

            AdaptiveColor.delays.append(delay)
            first_delay = AdaptiveColor.delays.pop(0)
            AdaptiveColor.delay_avg += (delay - first_delay) / history_size

        delay_modifier = helper.renormalize(AdaptiveColor.delay_avg, AdaptiveColor.max_delay, AdaptiveColor.min_delay, 0, 1)

        if color_handler.pedals[2]:
            vel *= 0.7

        AdaptiveColor.vels.append(vel)
        first_vel = AdaptiveColor.vels.pop(0)
        AdaptiveColor.vel_avg += (vel - first_vel) / history_size
        vel_modifier = helper.renormalize(AdaptiveColor.vel_avg, 0.3, 0.9, 0, 1)

        if use_vel and use_speed:
            prog = (vel_modifier + delay_modifier * delays_weight) / (1 + delays_weight)
        elif use_vel:
            prog = vel_modifier
        elif use_speed:
            prog = delay_modifier
        else:
            prog = 0

        if hsv_lerp:
            return helper.hsv_lerp(start_col, end_col, prog)
        else:
            return helper.rgb_to_hsv(helper.rgb_lerp(start_col, end_col, prog))

color_handler.add(AdaptiveColor)

AdaptiveColor.add_setting(settings.ColorSetting("Start Color", (0, 255, 0)))
AdaptiveColor.add_setting(settings.ColorSetting("End Color", (255, 0, 0)))
AdaptiveColor.add_setting(settings.BoolSetting("Lerp Type", False, "RGB", "HSV"))
AdaptiveColor.add_setting(settings.BoolSetting("Global Hue", True))
AdaptiveColor.add_setting(settings.BoolSetting("Use Velocity", True))
AdaptiveColor.add_setting(settings.BoolSetting("Use Play Speed", True))
AdaptiveColor.add_setting(settings.NumberSetting("Speed Weight", 0.5, 2))
AdaptiveColor.add_setting(settings.IntSetting("History", 10, 30)).set_change_callback(AdaptiveColor.clear_history)