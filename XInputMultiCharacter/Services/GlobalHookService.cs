using System.Windows.Forms;
using Gma.System.MouseKeyHook;

namespace XInputMultiCharacter.Services;

/// <summary>
/// One process-wide low-level keyboard/mouse hook. Drives both the live input mapping
/// (when the shared source is Keyboard+Mouse) and the global player-switch hotkeys
/// (which always work off the keyboard, regardless of source mode).
/// </summary>
public class GlobalHookService : IDisposable
{
    private readonly IKeyboardMouseEvents _hook = Hook.GlobalEvents();

    public HashSet<Keys> PressedKeys { get; } = new();
    public HashSet<MouseButtons> PressedMouseButtons { get; } = new();

    public event EventHandler<KeyEventArgs>? RawKeyDown;
    public event EventHandler<MouseEventArgs>? RawMouseDown;

    public GlobalHookService()
    {
        _hook.KeyDown += (s, e) => { PressedKeys.Add(e.KeyCode); RawKeyDown?.Invoke(s, e); };
        _hook.KeyUp += (s, e) => PressedKeys.Remove(e.KeyCode);
        _hook.MouseDown += (s, e) => { PressedMouseButtons.Add(e.Button); RawMouseDown?.Invoke(s, e); };
        _hook.MouseUp += (s, e) => PressedMouseButtons.Remove(e.Button);
    }

    public void Dispose() => _hook.Dispose();
}
