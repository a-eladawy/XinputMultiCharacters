# XInput Multi-Character Player

Maps **one physical device** (keyboard+mouse, or one DirectInput controller) onto
**up to 6 virtual Xbox 360 controllers**, all connected simultaneously, with a
global keyboard shortcut to instantly switch which one is "hot." Built for
games where you swap between multiple owned characters with a single input
device (each character = its own controller slot as far as the game is concerned).

## How switching works

```
                         ┌─► Player 1 controller (idle, neutral state)
Your keyboard/mouse   ───┤─► Player 2 controller (ACTIVE — receiving live input)
   or one controller     ├─► Player 3 controller (idle)
                         ├─► ...
                         └─► Player 6 controller (idle)

              Alt+1 ... Alt+6 (global hotkey) → moves the "active" pointer
```

- All 6 virtual controllers are created and connected the moment the app
  starts (or via the "Connect All" button) — the game sees 6 controllers
  the whole time.
- Only the **active** slot's controller gets updated every tick from your
  real input.
- The moment you switch, the slot you just left is immediately reset to a
  neutral state (buttons up, sticks centered, triggers released) so it
  doesn't leave a character walking into a wall.
- Switching is a genuine **global hotkey** (via a low-level keyboard hook),
  so it works while your game has focus — you never need to alt-tab into
  this app to switch characters.

## Prerequisites

The following Python libraries:
- Tkinter
- Threading
- time
- json
- os
- math
- vgamepad
- pygame
- pynput
