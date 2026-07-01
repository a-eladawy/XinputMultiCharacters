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

1. Windows 10/11 (x64)
2. [.NET 8 SDK](https://dotnet.microsoft.com/download)
3. [ViGEmBus driver](https://github.com/ViGEm/ViGEmBus/releases) — install and reboot if prompted

> As with the earlier single-device version, this was written and reasoned
> through in a Linux sandbox, so I could not compile/run it myself (WPF +
> ViGEmBus are Windows-only). Treat the first build like a fresh checkout.

## Build & run

```powershell
cd XInputMultiCharacter
dotnet restore
dotnet build -c Release
dotnet run -c Release
```

Or open `XInputMultiCharacter.sln` in Visual Studio and press F5.

Publish a standalone `.exe`:

```powershell
dotnet publish XInputMultiCharacter\XInputMultiCharacter.csproj -c Release -r win-x64 --self-contained true -p:PublishSingleFile=true
```

## Using it

1. At the top, pick your **Source**: `KeyboardMouse` or `DirectInput` (then
   choose your physical controller from the dropdown). This is the *one*
   device that drives whichever character is currently active.
2. The app auto-connects all 6 virtual controllers on launch. In-game,
   assign Player 1's virtual pad to character 1, Player 2's to character 2,
   etc. (however your game lets you assign controllers to characters/slots).
3. Each of the 6 tabs is a character/player slot:
   - Rename it if you like (top-left text box).
   - Bind buttons/sticks/triggers with **Set**, just like before — these
     read from whichever device you picked as the Source.
   - Set its **Switch Hotkey** (defaults to Alt+1 through Alt+6).
   - **Make Active Now** lets you test switching without leaving the app.
   - **Copy Mapping To All Players** pushes this tab's bindings to the other
     5 — handy since most people want identical controls across characters
     and only the active pointer changes.
4. Play normally. Press your hotkey (e.g. Alt+3) anytime — even with the
   game focused — and control instantly moves to that character's virtual
   controller.

## Project layout

```
XInputMultiCharacter/
  Models/
    Enums.cs, InputBinding.cs        Same binding vocabulary as before
    HotkeyBinding.cs                 NEW: Ctrl/Alt/Shift + key combo for switching
    ControllerProfile.cs             Per-slot button/stick/trigger mapping (+ CopyBindingsFrom)
    PlayerSlot.cs                    NEW: one character = name + profile + hotkey + controller
    SharedInputSource.cs             NEW: the single device driving every slot
    XboxState.cs                     Computed controller state snapshot
  Services/
    VirtualControllerService.cs      ViGEmBus wrapper (unchanged)
    DirectInputService.cs            Enumerate/poll DirectInput devices (unchanged)
    GlobalHookService.cs             Global keyboard/mouse hook (unchanged)
    XboxStateEvaluator.cs            NEW: pure Evaluate(profile,...) / Apply(controller,...)
    MultiCharacterRuntime.cs         NEW: owns all 6 slots, the active pointer, and the hotkey listener
  Views/
    XboxControllerDiagram.xaml(.cs)  Live controller diagram (unchanged)
    PlayerSlotView.xaml(.cs)         NEW: per-slot UI — mapping rows, hotkey capture, active badge
  MainWindow.xaml(.cs)               NEW: global source picker, connect-all, 6 fixed tabs
```

## Notes & things to double check

- Same NuGet version caveat as before: if a pinned version isn't resolvable,
  bump to the latest 1.x/4.x/5.x of `Nefarius.ViGEm.Client` /
  `SharpDX.DirectInput` / `MouseKeyHook` — the API calls used here have been
  stable across recent releases.
- The switch hotkey is genuinely global, which means if you're typing a `1`
  while holding Alt inside *this app's* own text fields, it'll also trigger
  a switch — an edge case, not a concern during normal use.
- If your chosen hotkey key is itself part of a stick/button binding for the
  active input source, that's fine — hotkeys are keyboard-only and evaluated
  independently of whatever the active profile is reading.
- Want per-slot deadzones, JSON profile save/load, or DualShock4 output
  instead of Xbox 360? All of that hooks in cleanly at
  `XboxStateEvaluator`/`ControllerProfile` without touching the switching
  engine.
