import midi
import mido
import led
import math
import threading
from time import sleep, time

LONG_PRESS_TIME = 0.5
PEDAL_PULSE_TIME = 0.2

BEAT_NOTE = 21
BAR_NOTE = 22

# int(mido.second2tick(msg.time, midi_file.ticks_per_beat normally 48, mido.bpm2tempo(120)))

# base all the timings from bpm

def _pulse(v, range, speed=1):
    return v + range * math.cos((time() - Track.global_start_time) * speed * 2 * math.pi * (Track.bpm / 60))

class Track:
    global_playing = False
    global_start_time = None
    player_thread = None
    metronome = False
    bpm = 120
    last_time = None
    recording_track = None
    STOPPED = 0
    PLAYING = 1
    RECORDING = 2

    @staticmethod
    def start_player():
        if Track.global_playing: return
        Track.global_playing = True
        Track.global_start_time = time()
        player_thread = threading.Thread(target=Track.midi_thread)
        player_thread.daemon = True
        player_thread.start()

    @staticmethod
    def stop_player():
        Track.global_playing = False
        Track.global_start_time = None

    @staticmethod
    def update_player():
        if all(track.state == Track.STOPPED and track.next_state is None for track in _tracks) and not Track.metronome:
            Track.stop_player()
        else:
            Track.start_player()

    @staticmethod
    def midi_thread():
        Track.last_time = None
        while Track.global_playing:
            cur_time = time()

            t = ((cur_time - Track.global_start_time) / (240 / Track.bpm)) % 1
            if Track.last_time is not None:
                last_t = ((Track.last_time - Track.global_start_time) / (240 / Track.bpm)) % 1
            else:
                last_t = 1

            if t >= 0 and t < 0.5 and last_t > 0.5: #bar
                for track in _tracks: track.on_bar()

                if Track.metronome:
                    midi.send(mido.Message("note_on", channel=9, note=BAR_NOTE, velocity=64), False)

            if Track.metronome:
                if t >= 0.05 and last_t < 0.05:
                    midi.send(mido.Message("note_on", channel=9, note=BAR_NOTE, velocity=0), False)                    

                for i in range(1, 4):
                    if t >= 0.25 * i and last_t < 0.25 * i:
                        midi.send(mido.Message("note_on", channel=9, note=BEAT_NOTE, velocity=64), False)
                    if t >= 0.3 * i and last_t < 0.3 * i:
                        midi.send(mido.Message("note_on", channel=9, note=BEAT_NOTE, velocity=0), False)

            if Track.last_time is not None:
                for track in _tracks: track.play_section(cur_time - Track.last_time)
            Track.last_time = cur_time

            sleep(0.005)

    @staticmethod
    def set_metronome(v):
        Track.metronome = v
        Track.update_player()

    def __init__(self, track_id):
        self.track_id = track_id
        self.time_down = None
        self.long_pressed = False
        self.state = Track.STOPPED
        self.has_recording = False
        self.next_state = None
        self.events = []
        self.bar_duration = 0
        self.bar_position = 0
        self.event_index = 0
        self.record_start_time = None
        self.playing_time = 0

    def get_state_color(self, state, static=False):
        if state == Track.STOPPED: return ((0, 0, 30) if self.has_recording else None)
        if state == Track.PLAYING: return (0, _pulse(50, 30, 0 if static else 1), 0)
        if state == Track.RECORDING: return (_pulse(50, 30, 0 if static else 1), 0, 0)

    def get_color(self):
        m = Track.bpm / 240
        if self.next_state is not None and time() % m < m / 2:
            return self.get_state_color(self.next_state)
        else:
            return self.get_state_color(self.state, self.next_state is not None)

    def record(self):
        for track in _tracks:
            if track.state == Track.RECORDING:
                track.state = Track.PLAYING

        self.state = Track.RECORDING
        self.record_start_time = time()
        self.has_recording = True
        Track.recording_track = self
        
    def add_event(self, msg):
        t = (time() - self.record_start_time) * Track.bpm
        msg = msg.copy()
        msg.time = t
        n_events = len(self.events)
        index = 0
        for i in range(n_events):
            if self.events[i][0].time > t: break
            index = i + 1

        self.events.insert(index, [msg, True])

    def play_section(self, dt):
        if self.state == Track.STOPPED: return

        self.playing_time = self.playing_time + dt
        for i in range(self.event_index, len(self.events)):
            msg, ignore = self.events[i]
            if self.playing_time < msg.time / Track.bpm:
                break
            self.event_index += 1
            if ignore:
                self.events[i][1] = False
            else:
                midi.send(msg)

    def on_bar(self):
        self.trigger_next_state()

        if self.state != Track.STOPPED:
            self.bar_position += 1
            if self.bar_position > self.bar_duration:
                self.bar_position = 1
                self.event_index = 0
                self.playing_time = 0
                if self.state == Track.RECORDING:
                    self.record_start_time = time()
        
    def trigger_next_state(self):
        if self.next_state is not None:
            self.state = self.next_state
            if self.state == Track.STOPPED:
                self.bar_position = 0
                self.event_index = 0
                self.playing_time = 0
            if self.state == Track.RECORDING:
                self.record()
            else:
                if Track.recording_track == self:
                    Track.recording_track = None
                self.record_start_time = None
            self.next_state = None

            Track.update_player()

    def set_state(self, state, now=False):
        self.next_state = state
        if now or not Track.global_playing:
            self.trigger_next_state()

    def short_press(self, bar_duration):
        if self.state == Track.STOPPED:
            if self.has_recording:
                self.set_state(Track.PLAYING)
            else:
                self.bar_duration = bar_duration
                self.set_state(Track.RECORDING)
        elif self.state == Track.PLAYING:
            self.set_state(self.STOPPED)
        elif self.state == Track.RECORDING:
            self.set_state(Track.PLAYING)

    def long_press(self):
        if self.state == Track.STOPPED and self.has_recording:
            self.clear_recording()
        elif self.state == Track.PLAYING:
            self.set_state(Track.RECORDING)

    def clear_recording(self):
        self.has_recording = False
        self.bar_duration = 0
        self.events = []

    def key_change(self, down, bar_duration):
        if down:
            self.time_down = time()
        else:
            self.time_down = None
            if self.long_pressed:
                self.long_pressed = False
            else:
                self.short_press(bar_duration)

_pedal_down = False
_pedal_down_time = None
_pedal_last_hit = None
_hold_lights = False

_led_handle = led.LedHandle(False, True)

_tracks = [Track(i) for i in range(5)]

def _looper_handler(msg):
    global _pedal_down, _pedal_down_time, _pedal_last_hit, _hold_lights

    if msg.type == "control_change" and msg.control == 65:
        if msg.channel != 0: return

        _pedal_down = msg.value > 0
        midi.set_local(not _pedal_down)
        t = time()
        if _pedal_down:
            _led_handle.enable()
            _pedal_down_time = t
        else:
            if not _hold_lights:
                _led_handle.disable()

            if t - _pedal_down_time < PEDAL_PULSE_TIME:
                if _pedal_last_hit is not None and time() - _pedal_last_hit > 1:
                    _pedal_last_hit = None

                if _pedal_last_hit is not None:
                    diff = _pedal_down_time - _pedal_last_hit
                    Track.bpm = 60 / diff
                    if Track.global_playing:
                        Track.global_start_time = t
                        Track.last_time = None


                _pedal_last_hit = _pedal_down_time

        return

    if _pedal_down:
        if msg.type != "note_on": return
        note = msg.note - 21

        if note >= 15 and note <= 74:
            track_idx = math.floor((note - 15) / 12)
            track_loop_count = note - 15 - (track_idx * 12) + 1
            print(track_idx, track_loop_count)
            track = _tracks[track_idx]
            track.key_change(msg.velocity > 0, track_loop_count)

        if note == 0 and msg.velocity > 0:
            Track.set_metronome(not Track.metronome)

        if note == 87 and msg.velocity > 0:
            _hold_lights = not _hold_lights

    else:
        track = Track.recording_track
        if not track: return
        track.add_event(msg)

def _update_lights_ui():
    for i in [5, 10, 78, 83]:
        _led_handle[i] = (30, 30, 30)

    for i in range(5):
        col = _tracks[i].get_color() or (0, 0, 0)
        idx = 20 + (i * 10)
        half_col = (col[0] * 0.5, col[1] * 0.5, col[2] * 0.5)

        _led_handle[idx] = half_col
        _led_handle[idx + 9] = half_col
        _led_handle[idx + 3] = col
        _led_handle[idx + 6] = col

    if Track.global_playing:
        t = time() - Track.global_start_time
        bar_length = 4 / (Track.bpm / 60)
        prog = (t / bar_length) % 1

        if (prog * 8) % 2 > 1:
            _led_handle[1] = (0, 0, 0)
        else:
            if prog < 0.25:
                _led_handle[1] = (0, 100, 0)
            else:
                _led_handle[1] = (100, 0, 0)

    else:
        _led_handle[1] = (100, 0, 0)

    _led_handle.show()

def _handler():
    while True:
        for i in range(5):
            track = _tracks[i]
            if track.time_down and time() - track.time_down > LONG_PRESS_TIME:
                track.time_down = None
                track.long_pressed = True
                track.long_press()

        if _pedal_down or _hold_lights:
            _update_lights_ui()
        sleep(0.05)

btn_thread = threading.Thread(target=_handler)
btn_thread.daemon = True
btn_thread.start()
midi.add_callback(_looper_handler)