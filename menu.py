from gpiozero import Button
import screen
import math
import analog

_sub_menus = []
_sub_menu_index = -1
_temp_sub_menu = []

_btn = Button(17, hold_time=1, bounce_time=0.01)

_button_held = False

_old_val = -1.0

def _button_released():
    if _button_held: return
    if screen.wake(): return

    if len(_temp_sub_menu) > 0:
        _call_event("on_button_pressed")
    else:
        set_temp_sub_menu(_sub_menus[_sub_menu_index])
        _call_event("on_enter")
        _call_event("on_value_change", _old_val)

def _call_event(event, *args):
    if len(_temp_sub_menu) == 0: return
    sub_menu = _temp_sub_menu[len(_temp_sub_menu) - 1]

    if hasattr(sub_menu, event):
        getattr(sub_menu, event)(*args)

def _button_pressed():
    global _button_held
    _button_held = False

def _change_value(v):
    global _sub_menu_index
    global _old_val

    v = round(v, 2)

    diff = abs(_old_val - v)

    if not screen.is_awake():
        if diff <= 0.1: return
    else:
        if diff <= 0.01: return

    _old_val = v
    if screen.wake(): return

    if len(_temp_sub_menu) > 0:
        _call_event("on_value_change", v)
    else:
        old_index = _sub_menu_index
        _sub_menu_index = min(math.floor(v * len(_sub_menus)), len(_sub_menus) - 1)
        if old_index == _sub_menu_index: return
        _update_menu_screen()

def get_current_value():
    return _old_val

def _when_held():
    global _button_held
    _button_held = True
    if screen.wake(): return

    if len(_temp_sub_menu) > 0:
        _call_event("on_button_long_pressed")

def leave_sub_menu():
    _call_event("on_leave")
    _temp_sub_menu.pop()
    if len(_temp_sub_menu) > 0:
        _call_event("on_enter")
        _call_event("on_value_change", _old_val)
    else:
        _update_menu_screen()

def add_sub_menu(m):
	_sub_menus.append(m)

def set_temp_sub_menu(m):
    _temp_sub_menu.append(m)
    _call_event("on_enter")
    _call_event("on_value_change", _old_val)

def _update_menu_screen():
    screen.clear()
    screen.line1(_sub_menus[_sub_menu_index].name, True)
    select_text = "SELECT"
    if hasattr(_sub_menus[_sub_menu_index], "get_select_text"):
        select_text = _sub_menus[_sub_menu_index].get_select_text()
    screen.line2(select_text, True)

_call_queue = []

def _delay_call(f):
    def func(*args):
        _call_queue.append((f, args))
    return func

def loop():
    while len(_call_queue) > 0:
        (f, args) = _call_queue.pop(0)
        f(*args)

_btn.when_pressed = _delay_call(_button_pressed)
_btn.when_released = _delay_call(_button_released)
_btn.when_held = _delay_call(_when_held)
analog.set_callback(_delay_call(_change_value))

def init():
    analog.init()
    for m in _sub_menus:
    	if hasattr(m, "init"):
    		getattr(m, "init")()