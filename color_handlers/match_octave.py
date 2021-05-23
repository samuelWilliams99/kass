import settings
import color_handler
import octaves

class MatchOctave:
    name = "Match Octave"
    current_octave_note = 0

    @staticmethod
    def loop():
        pass

    @staticmethod
    def get_hsv(note, vel):
        high_note = octaves.last_octave_notes_preempt and octaves.last_octave_notes_preempt[1]
        if high_note and high_note <= MatchOctave.get_value("Cutoff Note"):
            MatchOctave.current_octave_note = high_note % 12
        return (MatchOctave.current_octave_note * (360/12), 1, 1)

color_handler.add(MatchOctave)

MatchOctave.add_setting(settings.NoteSetting("Cutoff Note", 35))