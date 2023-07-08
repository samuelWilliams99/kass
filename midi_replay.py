import menu
import screen
import settings
import midi
import mido
import math
import threading
from itertools import dropwhile
from os import walk, remove
from time import sleep, time
from pathlib import Path

_midi_history = []
_time_counter = 0
_last_message = None
_pedal_poses = [0, 0, 0]

_pedal_controls = [64, 66, 67]

_midi_path = "/home/pi/python/midi_files/"
Path(_midi_path).mkdir(parents=True, exist_ok=True)

settings.add(settings.TimeSetting("Replay Length", 300, 600))
# the lambda is cuz _remove_all_files isnt defined yet
settings.add(settings.SpecialActionSetting("Clear Replays", lambda: _remove_all_files(), complete_message="FILES REMOVED"))

class Replay:
	name = "Save Replay"

	@staticmethod
	def on_enter():
		file_name = _save()
		if file_name is not None:
			screen.line2("SAVED " + file_name, True)
		else:
			screen.line2("NO DATA", True)
		sleep(1)
		menu.leave_sub_menu()

	@staticmethod		
	def init():
		midi.add_callback(_midi_handler, True)

class ReplayViewer:
	name = "View Replay"
	files = []
	file_index = 0
	active = False
	playing = False
	playing_midi_file = None

	@staticmethod
	def on_enter():
		_, _, file_names = next(walk(_midi_path), (None, None, []))
		if len(file_names) == 0:
			screen.line2("NO FILES", True)
			sleep(1)
			menu.leave_sub_menu()
		else:
			ReplayViewer.active = True
			ReplayViewer.file_index = 0
			ReplayViewer.files = sorted(file_names, key=lambda name: int(name[5:-5]))

	@staticmethod
	def on_leave():
		ReplayViewer.active = False

	@staticmethod
	def on_button_pressed():
		if not ReplayViewer.active: return
		file_name = ReplayViewer.files[ReplayViewer.file_index]
		file_path = _midi_path + file_name
		if ReplayViewer.playing:
			ReplayViewer.stop()
		else:
			ReplayViewer.play(mido.MidiFile(file_path))
		ReplayViewer.update_display()

	@staticmethod
	def on_button_long_pressed():
		if not ReplayViewer.active: return
		ReplayViewer.stop()
		menu.leave_sub_menu()

	@staticmethod
	def on_value_change(v):
		if not ReplayViewer.active or ReplayViewer.playing: return
		file_count = len(ReplayViewer.files)
		ReplayViewer.file_index = min(math.floor(v * file_count), file_count - 1)
		ReplayViewer.update_display()

	@staticmethod
	def update_display():
		screen.line1(ReplayViewer.files[ReplayViewer.file_index][:-5], True)
		screen.line2("PRESS TO " + ("STOP" if ReplayViewer.playing else "PLAY"), True)

	@staticmethod
	def play(midi_file):
		if ReplayViewer.playing: return

		ReplayViewer.playing_midi_file = midi_file
		ReplayViewer.playing = True
		playing_thread = threading.Thread(target=ReplayViewer.play_func)
		playing_thread.daemon = True
		playing_thread.start()

	@staticmethod
	def play_func():
		start_time = time()
		input_time = 0.0
		keys_down = [False] * 88

		for msg in ReplayViewer.playing_midi_file:
			input_time += msg.time

			playback_time = time() - start_time
			duration_to_next_event = input_time - playback_time

			while duration_to_next_event > 0.0 and ReplayViewer.playing:
				sleep_time = min(duration_to_next_event, 0.05)
				duration_to_next_event -= sleep_time
				sleep(sleep_time)

			if msg.type == "note_on":
				keys_down[msg.note - 21] = msg.velocity > 0
			
			if not ReplayViewer.playing:
				break

			if isinstance(msg, mido.MetaMessage):
				continue
			
			midi.send(msg)
		if ReplayViewer.playing:
			ReplayViewer.playing = False
			ReplayViewer.update_display()
		else:
			for i in range(88):
				if keys_down[i]:
					midi.send(mido.Message("note_on", channel=0, note=i+21, velocity=0, time=0))
					midi.send(mido.Message("note_on", channel=1, note=i+21, velocity=0, time=0))
			for control in _pedal_controls:
				midi.send(mido.Message("control_change", channel=0, control=control, value=0, time=0))
				midi.send(mido.Message("control_change", channel=1, control=control, value=0, time=0))


	def stop():
		ReplayViewer.playing = False
		ReplayViewer.playing_midi_file = None

def _remove_all_files():
	_, _, file_names = next(walk(_midi_path), (None, None, []))
	for filename in file_names:
		remove(_midi_path + filename)

def _save():
	global _midi_history, _time_counter
	midi_file = mido.MidiFile()
	midi_track = mido.MidiTrack()
	midi_file.tracks.append(midi_track)

	for i, pos in enumerate(_pedal_poses):
		midi_track.append(mido.Message("control_change", channel=0, control=_pedal_controls[i], value=pos, time=0))
		midi_track.append(mido.Message("control_change", channel=1, control=_pedal_controls[i], value=pos, time=0))

	first_msg = next(iter(_midi_history), None)

	if not first_msg:
		return

	first_msg.time = 0

	for msg in _midi_history:
		msg.time = int(mido.second2tick(msg.time, midi_file.ticks_per_beat, mido.bpm2tempo(120)))
		midi_track.append(msg)

	_, _, file_names = next(walk(_midi_path), (None, None, []))
	last_file = max(file_names, key=lambda name: int(name[5:-5]), default=None)
	if last_file:
		last_idx = int(last_file[5:-5])
	else:
		last_idx = -1

	new_name = "midi_" + str(last_idx + 1)
	
	midi_file.save(_midi_path + new_name + ".midi")

	_midi_history = []
	_time_counter = 0
	return new_name

def _get_pedal_idx(msg):
	if msg.type != "control_change": return
	if msg.control in _pedal_controls:
		return _pedal_controls.index(msg.control)

def _midi_handler(msg):
	global _time_counter, _last_message
	if ReplayViewer.playing: return

	c_time = time()

	if not _last_message:
		_last_message = c_time

	delay = c_time - _last_message
	_last_message = c_time

	_time_counter += delay
	msg.time = delay
	history_length = settings.get_value("Replay Length")

	_midi_history.append(msg)

	while _time_counter - history_length > 0:
		if len(_midi_history) < 2: break
		first_note_post_time = _midi_history[1].time # delay after first note is delay before second
		_time_counter -= first_note_post_time
		removed_msg = _midi_history.pop(0)

		pedal_idx = _get_pedal_idx(removed_msg)
		if pedal_idx is not None:
			_pedal_poses[pedal_idx] = removed_msg.value
