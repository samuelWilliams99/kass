import screen
from time import sleep

def greet():
	screen.clear()

	screen.add_custom_char(0, [
		"     ",
		" XXX ",
		"X   X",
		"     ",
		"     ",
		"     ",
		"     ",
		"     "
		])

	screen.add_custom_char(1, [
		"     ",
		"     ",
		"     ",
		"     ",
		"X   X",
		" XXX ",
		"     ",
		"     "
		])

	screen.add_custom_char(2, [
		"     ",
		"X    ",
		" X   ",
		"  X  ",
		" X   ",
		" X   ",
		"X    ",
		"     "
		])

	screen.add_custom_char(3, [
		"     ",
		"  X  ",
		"  X  ",
		"  X  ",
		" X   ",
		" X   ",
		"X    ",
		"     "
		])

	screen.add_custom_char(4, [
		"     ",
		"    X",
		"   X ",
		"  X  ",
		" X   ",
		" X   ",
		"X    ",
		"     "
		])

	screen.clear()
	sleep(0.2)
	screen.line1("Hi, I'm Kass!", True, True)
	_wave()
	_wave()
	screen.clear()
	sleep(0.5)

def _wave():
	screen.line2("\x00\x01\x00\x02", True)
	sleep(0.2)
	screen.line2("\x00\x01\x00\x03", True)
	sleep(0.1)
	screen.line2("\x00\x01\x00\x04", True)
	sleep(0.2)
	screen.line2("\x00\x01\x00\x03", True)
	sleep(0.1)
