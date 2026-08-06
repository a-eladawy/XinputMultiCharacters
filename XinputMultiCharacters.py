#!/usr/bin/env python3
"""
XInput Multi Character Player (Optimized & Updated)
==================================================
One input device controls multiple virtual Xbox 360 controllers simultaneously,
but only ONE is active at a time. Use configurable switch hotkeys to toggle
the active player.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import math
from typing import Optional, List, Dict, Set, Tuple, Callable
from dataclasses import dataclass, field
from copy import deepcopy

# =============================================================================
# OPTIONAL DEPENDENCIES
# =============================================================================
PYGAME_AVAILABLE = False
VIGEM_AVAILABLE = False
PYNPUT_AVAILABLE = False

try:
    import vgamepad as vg
    VIGEM_AVAILABLE = True
except ImportError:
    vg = None

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None

try:
    from pynput import keyboard as kb_listener
    from pynput import mouse as ms_listener
    PYNPUT_AVAILABLE = True
except ImportError:
    kb_listener = None
    ms_listener = None


# =============================================================================
# CONSTANTS
# =============================================================================
MAX_CONTROLLERS = 6
STICK_MAX = 32767
TRIGGER_MAX = 255
DEADZONE = 0.15
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xinput_multiplayer_config.json")

BUTTON_NAMES = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'BACK', 'START', 'GUIDE', 'LEFT_THUMB', 'RIGHT_THUMB',
                'DPAD_UP', 'DPAD_DOWN', 'DPAD_LEFT', 'DPAD_RIGHT']

if VIGEM_AVAILABLE:
    BUTTON_MAP = {
        'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
        'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
        'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
        'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        'LB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
        'RB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
        'BACK': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
        'GUIDE': vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
        'LEFT_THUMB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
        'RIGHT_THUMB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
        'DPAD_UP': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        'DPAD_DOWN': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
        'DPAD_LEFT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
        'DPAD_RIGHT': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    }
else:
    BUTTON_MAP = {}


# =============================================================================
# DEFAULT KEY BINDINGS & HOTKEYS (UPDATED)
# =============================================================================
DEFAULT_BINDINGS = {
    # Left stick (Arrow keys)
    'w': ('left_stick_y', 1.0),
    's': ('left_stick_y', -1.0),
    'a': ('left_stick_x', -1.0),
    'd': ('left_stick_x', 1.0),

    # Right stick (P, ;, L, ')
    'y': ('right_stick_y', 1.0),
    'j': ('right_stick_y', -1.0),
    'g': ('right_stick_x', -1.0),
    "h": ('right_stick_x', 1.0),

    # Triggers & Bumpers
    '1': ('left_trigger', 1.0),
    '3': ('right_trigger', 1.0),
    'q': 'LB',
    'e': 'RB',

    # Action Buttons
    'k': 'A',
    'o': 'B',
    'i': 'X',
    'l': 'Y',

    # D-Pad
    'up': 'DPAD_UP',
    'down': 'DPAD_DOWN',
    'left': 'DPAD_LEFT',
    'right': 'DPAD_RIGHT',

    # System Buttons
    '9': 'BACK',
    'esc': 'START',
    '0': 'START',
    '-': 'GUIDE',

    # Thumb Clicks
    'z': 'LEFT_THUMB',
    'b': 'RIGHT_THUMB',
}

DEFAULT_SWITCH_HOTKEYS = ['delete', 'page_up', 'page_down', '[', ']', '/']


# =============================================================================
# CONFIG MANAGEMENT
# =============================================================================
class ConfigManager:
    @staticmethod
    def load() -> Dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    bindings = data.get('bindings', {})
                    for k, v in bindings.items():
                        if isinstance(v, list) and len(v) == 2:
                            bindings[k] = (v[0], v[1])
                    return {
                        'bindings': bindings,
                        'switch_hotkeys': data.get('switch_hotkeys', list(DEFAULT_SWITCH_HOTKEYS))
                    }
            except Exception:
                pass
        return {'bindings': deepcopy(DEFAULT_BINDINGS), 'switch_hotkeys': list(DEFAULT_SWITCH_HOTKEYS)}

    @staticmethod
    def save(bindings: Dict, switch_hotkeys: List[str]):
        try:
            serializable = {}
            for k, v in bindings.items():
                if isinstance(v, tuple):
                    serializable[k] = [v[0], v[1]]
                else:
                    serializable[k] = v
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'bindings': serializable, 'switch_hotkeys': switch_hotkeys}, f, indent=2)
        except Exception as e:
            print(f"Config save error: {e}")


# =============================================================================
# CONTROLLER STATE
# =============================================================================
@dataclass
class ControllerState:
    left_stick_x: float = 0.0
    left_stick_y: float = 0.0
    right_stick_x: float = 0.0
    right_stick_y: float = 0.0
    left_trigger: float = 0.0
    right_trigger: float = 0.0
    buttons: Set[str] = field(default_factory=set)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def reset(self):
        with self.lock:
            self.left_stick_x = 0.0
            self.left_stick_y = 0.0
            self.right_stick_x = 0.0
            self.right_stick_y = 0.0
            self.left_trigger = 0.0
            self.right_trigger = 0.0
            self.buttons.clear()


# =============================================================================
# VIRTUAL XINPUT DEVICE
# =============================================================================
class VirtualXboxController:
    def __init__(self, controller_id: int):
        self.id = controller_id
        self.gamepad = None
        self.state = ControllerState()
        self.active = False
        self.enabled = True
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def connect(self) -> bool:
        if not VIGEM_AVAILABLE or not self.enabled:
            return False
        if self.active:
            return True
        try:
            self.gamepad = vg.VX360Gamepad()
            self.active = True
            self._stop.clear()
            self._thread = threading.Thread(target=self._update_loop, daemon=True)
            self._thread.start()
            return True
        except Exception as e:
            print(f"[Controller {self.id+1}] Connect failed: {e}")
            return False

    def disconnect(self):
        self._stop.set()
        self.active = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self.gamepad:
            try:
                self.gamepad.reset()
                self.gamepad.update()
            except Exception:
                pass
            self.gamepad = None

    def _update_loop(self):
        while not self._stop.is_set():
            try:
                with self.state.lock:
                    self.gamepad.left_joystick(
                        int(self.state.left_stick_x * STICK_MAX),
                        int(self.state.left_stick_y * STICK_MAX)
                    )
                    self.gamepad.right_joystick(
                        int(self.state.right_stick_x * STICK_MAX),
                        int(self.state.right_stick_y * STICK_MAX)
                    )
                    self.gamepad.left_trigger(int(self.state.left_trigger * TRIGGER_MAX))
                    self.gamepad.right_trigger(int(self.state.right_trigger * TRIGGER_MAX))
                    for name, btn in BUTTON_MAP.items():
                        if name in self.state.buttons:
                            self.gamepad.press_button(btn)
                        else:
                            self.gamepad.release_button(btn)
                    self.gamepad.update()
            except Exception as e:
                print(f"[Controller {self.id+1}] Update error: {e}")
            time.sleep(0.008)


# =============================================================================
# INPUT ROUTER
# =============================================================================
class InputRouter:
    def __init__(self, controllers: List[VirtualXboxController]):
        self.controllers = controllers
        self.active_index = 0
        self._lock = threading.Lock()
        self._source: Optional['InputSource'] = None
        self._running = False

    def set_active(self, index: int):
        if not (0 <= index < len(self.controllers)):
            return
        with self._lock:
            old = self.active_index
            if old != index:
                self.controllers[old].state.reset()
            self.active_index = index

    def get_active(self) -> int:
        with self._lock:
            return self.active_index

    def update_axes_state(self, lx: float, ly: float, rx: float, ry: float, lt: float, rt: float):
        l_len = math.hypot(lx, ly)
        if l_len > 1.0:
            lx /= l_len
            ly /= l_len

        r_len = math.hypot(rx, ry)
        if r_len > 1.0:
            rx /= r_len
            ry /= r_len

        with self._lock:
            target = self.controllers[self.active_index].state
        with target.lock:
            target.left_stick_x = lx
            target.left_stick_y = ly
            target.right_stick_x = rx
            target.right_stick_y = ry
            target.left_trigger = lt
            target.right_trigger = rt

    def apply_button(self, button_name: str, pressed: bool):
        with self._lock:
            target = self.controllers[self.active_index].state
        with target.lock:
            if pressed:
                target.buttons.add(button_name)
            else:
                target.buttons.discard(button_name)

    def start_source(self, source: 'InputSource'):
        self._source = source
        self._running = True
        source.start(self)

    def stop(self):
        self._running = False
        if self._source:
            self._source.stop()
            self._source = None
        for c in self.controllers:
            c.state.reset()


# =============================================================================
# INPUT SOURCES
# =============================================================================
class InputSource:
    def start(self, router: InputRouter): ...
    def stop(self): ...


class KeyboardMouseSource(InputSource):
    def __init__(self, bindings: Dict, switch_hotkeys: List[str], mouse_enabled: bool = False):
        self.bindings = bindings
        self.switch_hotkeys = switch_hotkeys
        self.mouse_enabled = mouse_enabled
        self.router: Optional[InputRouter] = None
        self._kb_listener = None
        self._mouse_listener = None
        self._pressed_keys: Set[str] = set()
        self._lock = threading.Lock()
        self._mouse_x = 0.0
        self._mouse_y = 0.0
        self._last_mouse_time = 0.0
        self._running = False
        self._input_thread: Optional[threading.Thread] = None

    def _normalize_key(self, key) -> str:
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char.lower()
        except AttributeError:
            pass
        key_str = str(key).replace('Key.', '').lower()
        if key_str in ('alt_l', 'alt_r', 'alt_gr'): return 'alt'
        if key_str in ('shift_l', 'shift_r'): return 'shift'
        if key_str in ('ctrl_l', 'ctrl_r'): return 'ctrl'
        if key_str in ('cmd', 'cmd_l', 'cmd_r', 'win', 'win_l', 'win_r'): return 'command'
        if key_str == 'del': return 'delete'
        if key_str == 'page_up': return 'page_up'
        if key_str == 'page_down': return 'page_down'
        return key_str

    def start(self, router: InputRouter):
        if not PYNPUT_AVAILABLE:
            return
        self.router = router
        self._running = True
        self._pressed_keys.clear()

        def on_press(key):
            k = self._normalize_key(key)
            self._handle_key(k, True)

        def on_release(key):
            k = self._normalize_key(key)
            self._handle_key(k, False)

        self._kb_listener = kb_listener.Listener(on_press=on_press, on_release=on_release)
        self._kb_listener.start()

        def on_move(x, y):
            if not self._running or self.router is None or not self.mouse_enabled:
                return
            now = time.time()
            dt = now - self._last_mouse_time if self._last_mouse_time else 0.016
            self._last_mouse_time = now
            sens = 0.008
            with self._lock:
                self._mouse_x += x * sens * dt
                self._mouse_y += y * sens * dt
                self._mouse_x = max(-1.0, min(1.0, self._mouse_x))
                self._mouse_y = max(-1.0, min(1.0, self._mouse_y))

        def on_click(x, y, button, pressed):
            if not self._running or self.router is None or not self.mouse_enabled:
                return
            if button == ms_listener.Button.left:
                self.router.apply_button('right_trigger', pressed)
            elif button == ms_listener.Button.right:
                self.router.apply_button('left_trigger', pressed)

        self._mouse_listener = ms_listener.Listener(on_move=on_move, on_click=on_click)
        self._mouse_listener.start()

        self._input_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._input_thread.start()

    def _handle_key(self, key_name: str, pressed: bool):
        if not self._running or self.router is None:
            return

        with self._lock:
            if pressed:
                self._pressed_keys.add(key_name)
            else:
                self._pressed_keys.discard(key_name)

        if pressed and key_name in self.switch_hotkeys:
            idx = self.switch_hotkeys.index(key_name)
            self.router.set_active(idx)
            return

        action = self.bindings.get(key_name)
        if isinstance(action, str):
            self.router.apply_button(action, pressed)

    def _process_loop(self):
        while self._running:
            time.sleep(0.008)
            if self.router is None:
                continue

            lx, ly = 0.0, 0.0
            rx, ry = 0.0, 0.0
            lt, rt = 0.0, 0.0

            with self._lock:
                active_keys = list(self._pressed_keys)

            for k in active_keys:
                action = self.bindings.get(k)
                if isinstance(action, tuple) and len(action) == 2:
                    axis, val = action
                    if axis == 'left_stick_x': lx += val
                    elif axis == 'left_stick_y': ly += val
                    elif axis == 'right_stick_x': rx += val
                    elif axis == 'right_stick_y': ry += val
                    elif axis == 'left_trigger': lt = max(lt, val)
                    elif axis == 'right_trigger': rt = max(rt, val)

            if self.mouse_enabled:
                with self._lock:
                    self._mouse_x *= 0.85
                    self._mouse_y *= 0.85
                    if abs(self._mouse_x) < 0.02: self._mouse_x = 0.0
                    if abs(self._mouse_y) < 0.02: self._mouse_y = 0.0
                    mx, my = self._mouse_x, self._mouse_y
                if rx == 0.0 and ry == 0.0:
                    rx, ry = mx, my
            else:
                with self._lock:
                    self._mouse_x = 0.0
                    self._mouse_y = 0.0

            self.router.update_axes_state(
                max(-1.0, min(1.0, lx)),
                max(-1.0, min(1.0, ly)),
                max(-1.0, min(1.0, rx)),
                max(-1.0, min(1.0, ry)),
                max(0.0, min(1.0, lt)),
                max(0.0, min(1.0, rt))
            )

    def stop(self):
        self._running = False
        if self._kb_listener:
            self._kb_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
        self.router = None


class DInputSource(InputSource):
    def __init__(self, device_index: int):
        self.device_index = device_index
        self.joystick = None
        self.router: Optional[InputRouter] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self, router: InputRouter):
        if not PYGAME_AVAILABLE or pygame is None:
            return
        self.router = router
        try:
            pygame.joystick.init()
            self.joystick = pygame.joystick.Joystick(self.device_index)
            self.joystick.init()
            self._running = True
            self._thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            print(f"[DInput {self.device_index}] Start failed: {e}")

    def _poll_loop(self):
        if not self.joystick or not self.router:
            return
        joy = self.joystick
        while self._running:
            try:
                pygame.event.pump()
                num_axes = joy.get_numaxes()
                num_buttons = joy.get_numbuttons()

                lx = self._dz(joy.get_axis(0)) if num_axes >= 1 else 0.0
                ly = self._dz(-joy.get_axis(1)) if num_axes >= 2 else 0.0
                rx = self._dz(joy.get_axis(3)) if num_axes >= 4 else 0.0
                ry = self._dz(-joy.get_axis(4)) if num_axes >= 5 else 0.0
                lt = max(0.0, min(1.0, (joy.get_axis(2) + 1.0) / 2.0)) if num_axes >= 3 else 0.0
                rt = max(0.0, min(1.0, (joy.get_axis(5) + 1.0) / 2.0)) if num_axes >= 6 else 0.0

                self.router.update_axes_state(lx, ly, rx, ry, lt, rt)

                btn_map = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'BACK', 'START', 'LEFT_THUMB', 'RIGHT_THUMB']
                for i in range(min(num_buttons, len(btn_map))):
                    self.router.apply_button(btn_map[i], bool(joy.get_button(i)))

                if joy.get_numhats() > 0:
                    hx, hy = joy.get_hat(0)
                    self.router.apply_button('DPAD_UP', hy > 0)
                    self.router.apply_button('DPAD_DOWN', hy < 0)
                    self.router.apply_button('DPAD_LEFT', hx < 0)
                    self.router.apply_button('DPAD_RIGHT', hx > 0)

            except Exception as e:
                print(f"[DInput {self.device_index}] Poll error: {e}")
            time.sleep(0.004)

    def _dz(self, val: float) -> float:
        if abs(val) < DEADZONE:
            return 0.0
        sign = 1.0 if val > 0 else -1.0
        return sign * min(1.0, (abs(val) - DEADZONE) / (1.0 - DEADZONE))

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        if self.joystick:
            self.joystick.quit()
            self.joystick = None
        self.router = None


# =============================================================================
# MINI CONTROLLER DIAGRAM (WITH CONNECTOR CHECKBOXES)
# =============================================================================
class MiniDiagram:
    BODY = "#2d2d2d"
    BODY_OUTLINE = "#404040"
    ACTIVE_GLOW = "#00ff88"
    INACTIVE_BORDER = "#333333"
    BTN_A = "#3cb043"
    BTN_B = "#e03030"
    BTN_X = "#3078e0"
    BTN_Y = "#e0d030"
    BTN_DEFAULT = "#555555"
    BTN_ACTIVE = "#ffffff"
    STICK_BG = "#1a1a1a"
    STICK_FG = "#888888"
    TRIGGER_FG = "#e0a030"
    DPAD_BG = "#1a1a1a"
    DPAD_ACTIVE = "#888888"

    def __init__(self, canvas: tk.Canvas, x: int, y: int, scale: float = 1.0, player_num: int = 1, on_click=None, on_toggle_enable=None):
        self.canvas = canvas
        self.ox = x
        self.oy = y
        self.scale = scale
        self.player_num = player_num
        self.on_click = on_click
        self.on_toggle_enable = on_toggle_enable
        self._items: Dict[str, int] = {}
        self.enabled_var = tk.BooleanVar(value=True)
        self._build()

    def _s(self, v: float) -> float:
        return v * self.scale

    def _build(self):
        c = self.canvas
        ox, oy = self.ox, self.oy
        s = self._s
        pn = self.player_num

        self._items['border'] = c.create_rectangle(
            ox - s(5), oy - s(5), ox + s(255), oy + s(175),
            outline=self.INACTIVE_BORDER, width=2, fill="", tags=(f'player_border_{pn}',)
        )
        self._click_rect = c.create_rectangle(
            ox - s(5), oy - s(5), ox + s(255), oy + s(140),
            fill="", outline="", tags=(f'player_click_{pn}',)
        )
        c.tag_bind(f'player_click_{pn}', '<Button-1>', lambda e: self._on_click())
        c.tag_bind(f'player_border_{pn}', '<Enter>', lambda e: c.config(cursor='hand2'))
        c.tag_bind(f'player_border_{pn}', '<Leave>', lambda e: c.config(cursor=''))
        c.tag_bind(f'player_click_{pn}', '<Enter>', lambda e: c.config(cursor='hand2'))
        c.tag_bind(f'player_click_{pn}', '<Leave>', lambda e: c.config(cursor=''))
        
        self._items['body'] = c.create_oval(
            ox + s(30), oy + s(20), ox + s(220), oy + s(140),
            fill=self.BODY, outline=self.BODY_OUTLINE, width=2
        )
        c.create_oval(
            ox + s(105), oy + s(50), ox + s(145), oy + s(110),
            fill=self.BODY, outline=self.BODY_OUTLINE, width=1
        )
        self._draw_stick('ls', 75, 80)
        self._draw_stick('rs', 175, 100)
        self._draw_dpad('dpad', 75, 110)
        self._draw_abxy('abxy', 175, 70)

        self._items['lb'] = c.create_rectangle(
            ox + s(40), oy + s(15), ox + s(80), oy + s(28),
            fill=self.BTN_DEFAULT, outline=self.BODY_OUTLINE, width=1
        )
        c.create_text(ox + s(60), oy + s(21), text="LB", fill="white", font=("Arial", 7, "bold"))
        self._items['rb'] = c.create_rectangle(
            ox + s(170), oy + s(15), ox + s(210), oy + s(28),
            fill=self.BTN_DEFAULT, outline=self.BODY_OUTLINE, width=1
        )
        c.create_text(ox + s(190), oy + s(21), text="RB", fill="white", font=("Arial", 7, "bold"))

        self._draw_trigger('lt', 60, 5, 30, 50)
        self._draw_trigger('rt', 190, 5, 30, 50)

        self._items['back'] = c.create_oval(ox + s(112), oy + s(57), ox + s(122), oy + s(67), fill=self.BTN_DEFAULT, outline=self.BODY_OUTLINE, width=1)
        self._items['start'] = c.create_oval(ox + s(128), oy + s(57), ox + s(138), oy + s(67), fill=self.BTN_DEFAULT, outline=self.BODY_OUTLINE, width=1)
        self._items['guide'] = c.create_oval(ox + s(118), oy + s(70), ox + s(132), oy + s(84), fill=self.BTN_DEFAULT, outline="#888888", width=1)
        c.create_text(ox + s(125), oy + s(77), text="X", fill="white", font=("Arial", 7, "bold"))

        self._items['label'] = c.create_text(
            ox + s(85), oy + s(155), text=f"Player {pn}", fill="#888888", font=("Arial", 10, "bold")
        )

        # Connect/Disconnect Toggle Checkbox
        chk = tk.Checkbutton(
            c.master, text="Connected", variable=self.enabled_var,
            bg="#1a1a1a", fg="white", selectcolor="#333333", activebackground="#1a1a1a",
            activeforeground="white", font=("Arial", 8), command=self._on_toggle
        )
        c.create_window(ox + s(195), oy + s(155), window=chk)

    def _on_toggle(self):
        if self.on_toggle_enable:
            self.on_toggle_enable(self.player_num - 1, self.enabled_var.get())

    def _draw_stick(self, name: str, cx: int, cy: int):
        c = self.canvas
        ox, oy = self.ox, self.oy
        s = self._s
        r = 20
        c.create_oval(ox + s(cx - r), oy + s(cy - r), ox + s(cx + r), oy + s(cy + r), fill=self.STICK_BG, outline=self.BODY_OUTLINE, width=1)
        self._items[f'{name}_fg'] = c.create_oval(
            ox + s(cx - 5), oy + s(cy - 5), ox + s(cx + 5), oy + s(cy + 5),
            fill=self.STICK_FG, outline="white", width=1
        )
        self._items[f'{name}_cx'] = cx
        self._items[f'{name}_cy'] = cy

    def _draw_dpad(self, name: str, cx: int, cy: int):
        c = self.canvas
        ox, oy = self.ox, self.oy
        s = self._s
        t, l = 4, 10
        self._items[f'{name}_up'] = c.create_polygon(
            ox + s(cx - t), oy + s(cy - l), ox + s(cx + t), oy + s(cy - l),
            ox + s(cx + t), oy + s(cy), ox + s(cx - t), oy + s(cy),
            fill=self.DPAD_BG, outline=self.BODY_OUTLINE
        )
        self._items[f'{name}_down'] = c.create_polygon(
            ox + s(cx - t), oy + s(cy), ox + s(cx + t), oy + s(cy),
            ox + s(cx + t), oy + s(cy + l), ox + s(cx - t), oy + s(cy + l),
            fill=self.DPAD_BG, outline=self.BODY_OUTLINE
        )
        self._items[f'{name}_left'] = c.create_polygon(
            ox + s(cx - l), oy + s(cy - t), ox + s(cx), oy + s(cy - t),
            ox + s(cx), oy + s(cy + t), ox + s(cx - l), oy + s(cy + t),
            fill=self.DPAD_BG, outline=self.BODY_OUTLINE
        )
        self._items[f'{name}_right'] = c.create_polygon(
            ox + s(cx), oy + s(cy - t), ox + s(cx + l), oy + s(cy - t),
            ox + s(cx + l), oy + s(cy + t), ox + s(cx), oy + s(cy + t),
            fill=self.DPAD_BG, outline=self.BODY_OUTLINE
        )

    def _draw_abxy(self, name: str, cx: int, cy: int):
        c = self.canvas
        ox, oy = self.ox, self.oy
        s = self._s
        r, off = 10, 14
        self._items['Y'] = c.create_oval(ox + s(cx - off - r), oy + s(cy - off - r), ox + s(cx - off + r), oy + s(cy - off + r), fill=self.BTN_Y, outline=self.BODY_OUTLINE, width=1)
        self._items['B'] = c.create_oval(ox + s(cx + off - r), oy + s(cy - r), ox + s(cx + off + r), oy + s(cy + r), fill=self.BTN_B, outline=self.BODY_OUTLINE, width=1)
        self._items['A'] = c.create_oval(ox + s(cx - r), oy + s(cy + off - r), ox + s(cx + r), oy + s(cy + off + r), fill=self.BTN_A, outline=self.BODY_OUTLINE, width=1)
        self._items['X'] = c.create_oval(ox + s(cx - off - r), oy + s(cy - r), ox + s(cx - off + r), oy + s(cy + r), fill=self.BTN_X, outline=self.BODY_OUTLINE, width=1)
        c.create_text(ox + s(cx - off), oy + s(cy - off), text="Y", fill="black", font=("Arial", 7, "bold"))
        c.create_text(ox + s(cx + off), oy + s(cy), text="B", fill="white", font=("Arial", 7, "bold"))
        c.create_text(ox + s(cx), oy + s(cy + off), text="A", fill="white", font=("Arial", 7, "bold"))
        c.create_text(ox + s(cx - off), oy + s(cy), text="X", fill="white", font=("Arial", 7, "bold"))

    def _draw_trigger(self, name: str, cx: int, cy: int, w: int, h: int):
        c = self.canvas
        ox, oy = self.ox, self.oy
        s = self._s
        self._items[f'{name}_bg'] = c.create_rectangle(ox + s(cx - w // 2), oy + s(cy), ox + s(cx + w // 2), oy + s(cy + h), fill=self.STICK_BG, outline=self.BODY_OUTLINE, width=1)
        self._items[f'{name}_fill'] = c.create_rectangle(ox + s(cx - w // 2 + 1), oy + s(cy + h - 2), ox + s(cx + w // 2 - 1), oy + s(cy + h), fill=self.TRIGGER_FG, outline="")
        c.create_text(ox + s(cx), oy + s(cy + h + 6), text=name.upper(), fill="white", font=("Arial", 6, "bold"))

    def update(self, state: ControllerState, is_active: bool, is_connected: bool):
        c = self.canvas
        if not is_connected:
            c.itemconfig(self._items['border'], outline="#552222", width=2)
            c.itemconfig(self._items['label'], fill="#666666", text=f"Player {self.player_num}  [OFF]")
        elif is_active:
            c.itemconfig(self._items['border'], outline=self.ACTIVE_GLOW, width=3)
            c.itemconfig(self._items['label'], fill=self.ACTIVE_GLOW, text=f"Player {self.player_num}  ACTIVE")
        else:
            c.itemconfig(self._items['border'], outline=self.INACTIVE_BORDER, width=2)
            c.itemconfig(self._items['label'], fill="#888888", text=f"Player {self.player_num}")

        with state.lock:
            self._update_stick('ls', state.left_stick_x, -state.left_stick_y)
            self._update_stick('rs', state.right_stick_x, -state.right_stick_y)
            self._update_trigger('lt', state.left_trigger)
            self._update_trigger('rt', state.right_trigger)
            btn_colors = {
                'A': self.BTN_A, 'B': self.BTN_B, 'X': self.BTN_X, 'Y': self.BTN_Y,
                'LB': self.BTN_DEFAULT, 'RB': self.BTN_DEFAULT,
                'BACK': self.BTN_DEFAULT, 'START': self.BTN_DEFAULT, 'GUIDE': self.BTN_DEFAULT,
                'LEFT_THUMB': self.STICK_FG, 'RIGHT_THUMB': self.STICK_FG,
            }
            for btn in ['A', 'B', 'X', 'Y', 'LB', 'RB', 'BACK', 'START', 'GUIDE', 'LEFT_THUMB', 'RIGHT_THUMB']:
                if btn in self._items:
                    c.itemconfig(self._items[btn], fill=self.BTN_ACTIVE if btn in state.buttons else btn_colors.get(btn, self.BTN_DEFAULT))
            for d in ['up', 'down', 'left', 'right']:
                item = self._items.get(f'dpad_{d}')
                if item:
                    active = f'DPAD_{d.upper()}' in state.buttons
                    c.itemconfig(item, fill=self.DPAD_ACTIVE if active else self.DPAD_BG)

    def _update_stick(self, name: str, x: float, y: float):
        c = self.canvas
        cx = self._items.get(f'{name}_cx', 0)
        cy = self._items.get(f'{name}_cy', 0)
        item = self._items.get(f'{name}_fg')
        if item:
            max_off = 12
            nx = self.ox + self._s(cx + x * max_off)
            ny = self.oy + self._s(cy + y * max_off)
            c.coords(item, nx - self._s(5), ny - self._s(5), nx + self._s(5), ny + self._s(5))

    def _update_trigger(self, name: str, val: float):
        c = self.canvas
        item = self._items.get(f'{name}_fill')
        bg = self._items.get(f'{name}_bg')
        if not item or not bg:
            return
        coords = c.coords(bg)
        if len(coords) < 4:
            return
        x1, y1, x2, y2 = coords
        height = y2 - y1
        fill_h = height * val
        new_y1 = y2 - fill_h
        c.coords(item, x1 + 1, new_y1, x2 - 1, y2 - 1)

    def _on_click(self):
        if self.on_click:
            self.on_click(self.player_num)


# =============================================================================
# REMAPPING DIALOG
# =============================================================================
class RemappingDialog:
    def __init__(self, parent: tk.Tk, bindings: Dict, switch_hotkeys: List[str], on_save: Callable):
        self.parent = parent
        self.bindings = deepcopy(bindings)
        self.switch_hotkeys = list(switch_hotkeys)
        self.on_save = on_save
        self.waiting_for_key: Optional[tk.StringVar] = None
        self.waiting_for_switch_idx: Optional[int] = None
        self.waiting_label: Optional[tk.Label] = None
        self._kb_listener = None
        self._window = None

    def show(self):
        self._window = tk.Toplevel(self.parent)
        self._window.title("Remap Controls")
        self._window.geometry("700x750")
        self._window.configure(bg="#1a1a1a")
        self._window.transient(self.parent)
        self._window.grab_set()

        tk.Label(self._window, text="Remap Controls", font=("Arial", 16, "bold"), bg="#1a1a1a", fg="white").pack(pady=10)
        tk.Label(self._window, text="Click a button then press the key you want to assign.", font=("Arial", 10), bg="#1a1a1a", fg="#aaaaaa").pack()
        tk.Label(self._window, text="Switch hotkeys will instantly swap active players.", font=("Arial", 9), bg="#1a1a1a", fg="#ff8888").pack(pady=(0, 10))

        canvas = tk.Canvas(self._window, bg="#1a1a1a", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self._window, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#1a1a1a")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        categories = [
            ("Player Switching Hotkeys", [
                ('switch_0', 'Switch to Player 1'),
                ('switch_1', 'Switch to Player 2'),
                ('switch_2', 'Switch to Player 3'),
                ('switch_3', 'Switch to Player 4'),
                ('switch_4', 'Switch to Player 5'),
                ('switch_5', 'Switch to Player 6'),
            ]),
            ("Left Stick", [
                ('left_stick_x_neg', 'Left'),
                ('left_stick_x_pos', 'Right'),
                ('left_stick_y_pos', 'Up'),
                ('left_stick_y_neg', 'Down'),
            ]),
            ("Right Stick", [
                ('right_stick_x_neg', 'Left'),
                ('right_stick_x_pos', 'Right'),
                ('right_stick_y_pos', 'Up'),
                ('right_stick_y_neg', 'Down'),
            ]),
            ("Triggers", [
                ('left_trigger', 'LT'),
                ('right_trigger', 'RT'),
            ]),
            ("Action Buttons", ['A', 'B', 'X', 'Y']),
            ("Shoulders", ['LB', 'RB']),
            ("D-Pad", ['DPAD_UP', 'DPAD_DOWN', 'DPAD_LEFT', 'DPAD_RIGHT']),
            ("System", ['BACK', 'START', 'GUIDE']),
            ("Stick Clicks", ['LEFT_THUMB', 'RIGHT_THUMB']),
        ]

        self._buttons: Dict[str, tk.Button] = {}

        for cat_name, actions in categories:
            cat_frame = tk.LabelFrame(scroll_frame, text=cat_name, bg="#252525", fg="white", font=("Arial", 11, "bold"), padx=10, pady=5)
            cat_frame.pack(fill=tk.X, pady=5, padx=5)

            for item in actions:
                row = tk.Frame(cat_frame, bg="#252525")
                row.pack(fill=tk.X, pady=2)

                if isinstance(item, tuple):
                    action_id, label_text = item
                else:
                    action_id = item
                    label_text = item.replace('_', ' ').title()

                tk.Label(row, text=label_text, bg="#252525", fg="white", font=("Arial", 10), width=20, anchor="w").pack(side=tk.LEFT)

                current_key = self._find_key_for_action(action_id)
                btn_text = current_key.upper() if current_key else "[Unbound]"

                btn = tk.Button(row, text=btn_text, width=15, bg="#333333", fg="white",
                                activebackground="#444444", activeforeground="white",
                                command=lambda a=action_id: self._start_capture(a))
                btn.pack(side=tk.LEFT, padx=5)
                self._buttons[action_id] = btn

                btn_clear = tk.Button(row, text="Clear", bg="#553333", fg="white",
                                      activebackground="#663333", activeforeground="white",
                                      command=lambda a=action_id: self._clear_mapping(a))
                btn_clear.pack(side=tk.LEFT, padx=2)

        btn_frame = tk.Frame(scroll_frame, bg="#1a1a1a")
        btn_frame.pack(fill=tk.X, pady=15)
        tk.Button(btn_frame, text="Reset to Defaults", bg="#553333", fg="white",
                  activebackground="#663333", command=self._reset_defaults).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save & Close", bg="#335533", fg="white",
                  activebackground="#336633", command=self._save).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Cancel", bg="#333333", fg="white",
                  activebackground="#444444", command=self._window.destroy).pack(side=tk.RIGHT, padx=5)

        if PYNPUT_AVAILABLE:
            def on_press(key):
                if self.waiting_for_key is None:
                    return
                try:
                    k = key.char.lower()
                except AttributeError:
                    k = str(key).replace('Key.', '').lower()
                if k == 'del': k = 'delete'
                self._finish_capture(k)

            self._kb_listener = kb_listener.Listener(on_press=on_press)
            self._kb_listener.start()

    def _find_key_for_action(self, action_id: str) -> Optional[str]:
        if action_id.startswith('switch_'):
            idx = int(action_id.split('_')[1])
            if idx < len(self.switch_hotkeys):
                return self.switch_hotkeys[idx]
            return None
        keys = self._find_all_keys_for_action(action_id)
        return keys[0] if keys else None

    def _start_capture(self, action_id: str):
        if self.waiting_for_key is not None and self.waiting_label:
            prev_action = self.waiting_for_key.get()
            key = self._find_key_for_action(prev_action)
            self.waiting_label.config(text=key.upper() if key else "[Unbound]", bg="#333333")

        self.waiting_for_key = tk.StringVar(value=action_id)
        if action_id.startswith('switch_'):
            self.waiting_for_switch_idx = int(action_id.split('_')[1])
        else:
            self.waiting_for_switch_idx = None

        btn = self._buttons.get(action_id)
        if btn:
            btn.config(text="Press a key...", bg="#555500")
            self.waiting_label = btn

    def _finish_capture(self, key_name: str):
        if self.waiting_for_key is None:
            return
        action_id = self.waiting_for_key.get()

        if self.waiting_for_switch_idx is not None:
            idx = self.waiting_for_switch_idx
            while key_name in self.switch_hotkeys:
                other_idx = self.switch_hotkeys.index(key_name)
                self.switch_hotkeys[other_idx] = ""
                other_btn = self._buttons.get(f'switch_{other_idx}')
                if other_btn:
                    other_btn.config(text="[Unbound]", bg="#333333")

            if key_name in self.bindings:
                del self.bindings[key_name]

            self.switch_hotkeys[idx] = key_name
            btn = self._buttons.get(action_id)
            if btn:
                btn.config(text=key_name.upper(), bg="#333333")
        else:
            if key_name in self.switch_hotkeys:
                other_idx = self.switch_hotkeys.index(key_name)
                self.switch_hotkeys[other_idx] = ""
                other_btn = self._buttons.get(f'switch_{other_idx}')
                if other_btn:
                    other_btn.config(text="[Unbound]", bg="#333333")

            if action_id.endswith('_pos'):
                axis = action_id[:-4]
                self.bindings[key_name] = (axis, 1.0)
            elif action_id.endswith('_neg'):
                axis = action_id[:-4]
                self.bindings[key_name] = (axis, -1.0)
            elif action_id in ('left_trigger', 'right_trigger'):
                self.bindings[key_name] = (action_id, 1.0)
            else:
                self.bindings[key_name] = action_id

            all_keys = self._find_all_keys_for_action(action_id)
            btn = self._buttons.get(action_id)
            if btn:
                display = ", ".join(k.upper() for k in all_keys) if all_keys else "[Unbound]"
                btn.config(text=display[:20], bg="#333333")

        self.waiting_for_key = None
        self.waiting_for_switch_idx = None
        self.waiting_label = None

    def _clear_mapping(self, action_id: str):
        if self.waiting_for_key is not None and self.waiting_for_key.get() == action_id:
            self.waiting_for_key = None
            self.waiting_for_switch_idx = None
            self.waiting_label = None

        if action_id.startswith('switch_'):
            idx = int(action_id.split('_')[1])
            if idx < len(self.switch_hotkeys):
                self.switch_hotkeys[idx] = ""
            btn = self._buttons.get(action_id)
            if btn:
                btn.config(text="[Unbound]", bg="#333333")
        else:
            keys_to_remove = self._find_all_keys_for_action(action_id)
            for k in keys_to_remove:
                if k in self.bindings:
                    del self.bindings[k]
            btn = self._buttons.get(action_id)
            if btn:
                btn.config(text="[Unbound]", bg="#333333")

    def _find_all_keys_for_action(self, action_id: str) -> List[str]:
        keys = []
        for k, v in self.bindings.items():
            if isinstance(v, tuple):
                axis, val = v
                if action_id.endswith('_pos') and val > 0 and axis == action_id[:-4]:
                    keys.append(k)
                elif action_id.endswith('_neg') and val < 0 and axis == action_id[:-4]:
                    keys.append(k)
                elif action_id == axis:
                    keys.append(k)
            elif v == action_id:
                keys.append(k)
        return keys

    def _reset_defaults(self):
        self.bindings = deepcopy(DEFAULT_BINDINGS)
        self.switch_hotkeys = list(DEFAULT_SWITCH_HOTKEYS)
        for action_id, btn in self._buttons.items():
            if action_id.startswith('switch_'):
                idx = int(action_id.split('_')[1])
                btn.config(text=self.switch_hotkeys[idx].upper() if self.switch_hotkeys[idx] else "[Unbound]", bg="#333333")
            else:
                keys = self._find_all_keys_for_action(action_id)
                display = ", ".join(k.upper() for k in keys) if keys else "[Unbound]"
                btn.config(text=display[:20], bg="#333333")

    def _save(self):
        self.on_save(self.bindings, self.switch_hotkeys)
        if self._kb_listener:
            self._kb_listener.stop()
        self._window.destroy()


# =============================================================================
# MAIN APPLICATION
# =============================================================================
class MultiPlayerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("XInput Multi Character Player")
        self.root.geometry("1100x720")
        self.root.minsize(950, 600)
        self.root.configure(bg="#1a1a1a")

        self.config = ConfigManager.load()
        self.bindings = self.config.get('bindings', deepcopy(DEFAULT_BINDINGS))
        self.switch_hotkeys = self.config.get('switch_hotkeys', list(DEFAULT_SWITCH_HOTKEYS))

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#1a1a1a")
        style.configure("TLabel", background="#1a1a1a", foreground="white")
        style.configure("TCombobox", fieldbackground="#333333", foreground="white")

        header = tk.Frame(root, bg="#252525", height=55)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)
        tk.Label(header, text="XInput Multi Character Player", font=("Arial", 16, "bold"), bg="#252525", fg="white").pack(side=tk.LEFT, padx=20, pady=10)
        self.status_var = tk.StringVar(value="All Disconnected")
        self.status_label = tk.Label(header, textvariable=self.status_var, font=("Arial", 10, "bold"), bg="#252525", fg="red")
        self.status_label.pack(side=tk.RIGHT, padx=20)

        ctrl = tk.Frame(root, bg="#1a1a1a")
        ctrl.pack(fill=tk.X, padx=15, pady=10)

        tk.Label(ctrl, text="Input Source:", font=("Arial", 10, "bold"), bg="#1a1a1a", fg="white").pack(side=tk.LEFT)
        self.source_type = tk.StringVar(value="None")
        self.src_combo = ttk.Combobox(ctrl, textvariable=self.source_type, values=["None", "Keyboard/Mouse", "DirectInput"], state="readonly", width=18)
        self.src_combo.pack(side=tk.LEFT, padx=5)
        self.src_combo.bind("<<ComboboxSelected>>", self._on_source_change)

        self.dinput_frame = tk.Frame(ctrl, bg="#1a1a1a")
        self.dinput_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(self.dinput_frame, text="Device:", bg="#1a1a1a", fg="white").pack(side=tk.LEFT)
        self.dinput_index = tk.IntVar(value=0)
        self.dinput_combo = ttk.Combobox(self.dinput_frame, textvariable=self.dinput_index, values=[], state="readonly", width=25)
        self.dinput_combo.pack(side=tk.LEFT, padx=5)
        tk.Button(self.dinput_frame, text="Refresh", command=self._refresh_dinput, bg="#333333", fg="white", activebackground="#444444").pack(side=tk.LEFT, padx=5)
        self.dinput_frame.pack_forget()

        tk.Button(ctrl, text="Remap Controls", bg="#335588", fg="white", activebackground="#4466aa",
                  command=self._open_remap).pack(side=tk.LEFT, padx=10)

        self.mouse_enabled = tk.BooleanVar(value=False)
        self.mouse_checkbox = tk.Checkbutton(ctrl, text="Mouse → R-Stick", variable=self.mouse_enabled,
                                              bg="#1a1a1a", fg="white", selectcolor="#333333",
                                              activebackground="#1a1a1a", activeforeground="white",
                                              command=self._on_mouse_toggle)
        self.mouse_checkbox.pack(side=tk.LEFT, padx=10)

        self.active_var = tk.StringVar(value="Active: Player 1")
        tk.Label(ctrl, textvariable=self.active_var, font=("Arial", 12, "bold"), bg="#1a1a1a", fg="#00ff88").pack(side=tk.RIGHT, padx=10)

        self.canvas = tk.Canvas(root, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.diagrams: List[MiniDiagram] = []
        self.controllers: List[VirtualXboxController] = []
        for i in range(MAX_CONTROLLERS):
            row = i // 3
            col = i % 3
            x = 20 + col * 360
            y = 20 + row * 260
            vc = VirtualXboxController(i)
            self.controllers.append(vc)
            diag = MiniDiagram(self.canvas, x, y, scale=0.9, player_num=i+1, 
                               on_click=self._on_player_click, 
                               on_toggle_enable=self._on_controller_toggle)
            self.diagrams.append(diag)

        self.router = InputRouter(self.controllers)

        info = tk.Frame(root, bg="#252525", height=70)
        info.pack(fill=tk.X, side=tk.BOTTOM)
        info.pack_propagate(False)
        txt = (
            "Switch Players: Del=P1  PgUp=P2  PgDn=P3  [=P4  ]=P5  /=P6  |  "
            "Arrows = Left Stick  |  P / ; / L / ' = Right Stick  |  "
            "Z/Enter=A  V/Backspace=B  C=X  X=Y  |  Q=LB  E=RB  |  A=LT  D=RT  |  "
            "0,9,7,8=D-Pad  |  1=Back  Esc/`=Start  2=Guide"
        )
        tk.Label(info, text=txt, font=("Consolas", 9), bg="#252525", fg="#aaaaaa", wraplength=1050, justify=tk.CENTER).pack(expand=True)
        tk.Label(info, text="Requires ViGEmBus. Not for kernel-level anti-cheat games.", font=("Arial", 8), bg="#252525", fg="#666666").pack()

        self._update_job = None
        self._start_ui_update()

        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _on_controller_toggle(self, index: int, enabled: bool):
        c = self.controllers[index]
        c.enabled = enabled
        if self.source_type.get() != "None":
            if enabled:
                c.connect()
            else:
                c.disconnect()
        self._update_status_label()

    def _update_status_label(self):
        if self.source_type.get() == "None":
            self.status_var.set("All Disconnected")
            self.status_label.config(fg="red")
        else:
            active_cnt = sum(1 for c in self.controllers if c.active)
            enabled_cnt = sum(1 for c in self.controllers if c.enabled)
            self.status_var.set(f"Connected {active_cnt}/{enabled_cnt} Enabled Controllers")
            self.status_label.config(fg="green" if active_cnt == enabled_cnt and enabled_cnt > 0 else "orange")

    def _on_source_change(self, event=None):
        src = self.source_type.get()
        self.router.stop()
        for c in self.controllers:
            c.disconnect()

        if src == "DirectInput":
            self.dinput_frame.pack(side=tk.LEFT, padx=10)
            self._refresh_dinput()
        else:
            self.dinput_frame.pack_forget()

        if src == "None":
            self._update_status_label()
            return

        if not VIGEM_AVAILABLE:
            messagebox.showerror("Missing Dependency", "vgamepad not installed.\nRun: pip install vgamepad")
            self.source_type.set("None")
            return

        for c in self.controllers:
            if c.enabled:
                c.connect()
        self._update_status_label()

        if src == "Keyboard/Mouse":
            if not PYNPUT_AVAILABLE:
                messagebox.showerror("Missing Dependency", "pynput not installed.\nRun: pip install pynput")
                self.source_type.set("None")
                self._on_source_change()
                return
            self._current_kms = KeyboardMouseSource(self.bindings, self.switch_hotkeys, mouse_enabled=self.mouse_enabled.get())
            self.router.start_source(self._current_kms)
        elif src == "DirectInput":
            if not PYGAME_AVAILABLE:
                messagebox.showerror("Missing Dependency", "pygame not installed.\nRun: pip install pygame")
                self.source_type.set("None")
                self._on_source_change()
                return
            idx = self.dinput_index.get()
            self.router.start_source(DInputSource(idx))

    def _refresh_dinput(self):
        if not PYGAME_AVAILABLE or pygame is None:
            return
        try:
            pygame.joystick.init()
            count = pygame.joystick.get_count()
            devices = []
            for i in range(count):
                try:
                    j = pygame.joystick.Joystick(i)
                    j.init()
                    devices.append(f"{i}: {j.get_name()}")
                    j.quit()
                except Exception:
                    devices.append(f"{i}: Unknown")
            self.dinput_combo.config(values=devices)
            if devices:
                self.dinput_combo.current(0)
            else:
                self.dinput_combo.set("No devices found")
        except Exception as e:
            self.dinput_combo.set(f"Error: {e}")

    def _on_mouse_toggle(self):
        if hasattr(self, '_current_kms') and self._current_kms:
            self._current_kms.mouse_enabled = self.mouse_enabled.get()

    def _open_remap(self):
        def on_save(new_bindings, new_switch_hotkeys):
            self.bindings = new_bindings
            self.switch_hotkeys = new_switch_hotkeys
            ConfigManager.save(self.bindings, self.switch_hotkeys)
            if self.source_type.get() == "Keyboard/Mouse":
                self.router.stop()
                self._current_kms = KeyboardMouseSource(self.bindings, self.switch_hotkeys, mouse_enabled=self.mouse_enabled.get())
                self.router.start_source(self._current_kms)

        dialog = RemappingDialog(self.root, self.bindings, self.switch_hotkeys, on_save)
        dialog.show()

    def _on_player_click(self, player_num: int):
        self.router.set_active(player_num - 1)

    def _start_ui_update(self):
        active = self.router.get_active()
        self.active_var.set(f"Active: Player {active + 1}")
        for i, (diag, ctrl) in enumerate(zip(self.diagrams, self.controllers)):
            diag.update(ctrl.state, is_active=(i == active), is_connected=ctrl.active)
        self._update_job = self.root.after(16, self._start_ui_update)

    def on_close(self):
        if self._update_job:
            self.root.after_cancel(self._update_job)
        self.router.stop()
        for c in self.controllers:
            c.disconnect()
        self.root.destroy()


def main():
    if not VIGEM_AVAILABLE:
        print("WARNING: vgamepad not installed. Virtual controllers will not work.")
        print("Install with: pip install vgamepad")
    if not PYGAME_AVAILABLE:
        print("WARNING: pygame not installed. DirectInput devices will not work.")
        print("Install with: pip install pygame")
    if not PYNPUT_AVAILABLE:
        print("WARNING: pynput not installed. Keyboard/Mouse mapping will not work.")
        print("Install with: pip install pynput")

    root = tk.Tk()
    app = MultiPlayerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
