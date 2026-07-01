using System.Windows.Forms;

namespace XInputMultiCharacter.Models;

/// <summary>A modifier-combo keyboard shortcut used to switch which player slot is "active".</summary>
public class HotkeyBinding
{
    public bool Ctrl { get; set; }
    public bool Alt { get; set; }
    public bool Shift { get; set; }
    public Keys Key { get; set; } = Keys.None;

    public static bool IsModifierKey(Keys k) =>
        k is Keys.LMenu or Keys.RMenu or Keys.Menu
          or Keys.LControlKey or Keys.RControlKey or Keys.ControlKey
          or Keys.LShiftKey or Keys.RShiftKey or Keys.ShiftKey;

    /// <summary>True if the currently-held modifier keys plus the just-pressed key match this hotkey.</summary>
    public bool Matches(HashSet<Keys> pressedKeys, Keys triggeredKey)
    {
        if (Key == Keys.None || Key != triggeredKey) return false;

        bool altHeld = pressedKeys.Contains(Keys.LMenu) || pressedKeys.Contains(Keys.RMenu) || pressedKeys.Contains(Keys.Menu);
        bool ctrlHeld = pressedKeys.Contains(Keys.LControlKey) || pressedKeys.Contains(Keys.RControlKey) || pressedKeys.Contains(Keys.ControlKey);
        bool shiftHeld = pressedKeys.Contains(Keys.LShiftKey) || pressedKeys.Contains(Keys.RShiftKey) || pressedKeys.Contains(Keys.ShiftKey);

        return altHeld == Alt && ctrlHeld == Ctrl && shiftHeld == Shift;
    }

    public override string ToString()
    {
        if (Key == Keys.None) return "Unbound";
        var parts = new List<string>();
        if (Ctrl) parts.Add("Ctrl");
        if (Alt) parts.Add("Alt");
        if (Shift) parts.Add("Shift");
        parts.Add(Key.ToString());
        return string.Join("+", parts);
    }
}
