using System.Windows.Forms;

namespace XInputMultiCharacter.Models;

public class StickBinding
{
    public InputBinding Up { get; set; } = new();
    public InputBinding Down { get; set; } = new();
    public InputBinding Left { get; set; } = new();
    public InputBinding Right { get; set; } = new();

    // If set to Kind = DIAxis, these override the digital Up/Down/Left/Right for analog movement.
    public InputBinding AxisX { get; set; } = new();
    public InputBinding AxisY { get; set; } = new();
}

public class TriggerBinding
{
    public InputBinding Digital { get; set; } = new();

    // If set to Kind = DIAxis or DISlider, overrides Digital with analog pull amount.
    public InputBinding Analog { get; set; } = new();
}

/// <summary>The button/stick/trigger mapping for one player slot's virtual controller.</summary>
public class ControllerProfile
{
    public Dictionary<XboxButton, InputBinding> ButtonBindings { get; } = new();
    public StickBinding LeftStick { get; } = new();
    public StickBinding RightStick { get; } = new();
    public TriggerBinding LeftTrigger { get; } = new();
    public TriggerBinding RightTrigger { get; } = new();

    public static ControllerProfile CreateDefaultKeyboardProfile()
    {
        var p = new ControllerProfile();

        InputBinding Key(Keys k) => new() { Kind = InputSourceKind.Keyboard, Code = (int)k };

        p.ButtonBindings[XboxButton.A] = Key(Keys.Space);
        p.ButtonBindings[XboxButton.B] = Key(Keys.LControlKey);
        p.ButtonBindings[XboxButton.X] = Key(Keys.Q);
        p.ButtonBindings[XboxButton.Y] = Key(Keys.E);
        p.ButtonBindings[XboxButton.LB] = Key(Keys.LShiftKey);
        p.ButtonBindings[XboxButton.RB] = Key(Keys.F);
        p.ButtonBindings[XboxButton.Back] = Key(Keys.Tab);
        p.ButtonBindings[XboxButton.Start] = Key(Keys.Escape);
        p.ButtonBindings[XboxButton.DPadUp] = Key(Keys.Up);
        p.ButtonBindings[XboxButton.DPadDown] = Key(Keys.Down);
        p.ButtonBindings[XboxButton.DPadLeft] = Key(Keys.Left);
        p.ButtonBindings[XboxButton.DPadRight] = Key(Keys.Right);

        p.LeftStick.Up = Key(Keys.W);
        p.LeftStick.Down = Key(Keys.S);
        p.LeftStick.Left = Key(Keys.A);
        p.LeftStick.Right = Key(Keys.D);

        return p;
    }

    /// <summary>Deep-copies every binding from another profile (used by "copy mapping to all players").</summary>
    public void CopyBindingsFrom(ControllerProfile other)
    {
        ButtonBindings.Clear();
        foreach (var kvp in other.ButtonBindings)
            ButtonBindings[kvp.Key] = kvp.Value.Clone();

        LeftStick.Up = other.LeftStick.Up.Clone();
        LeftStick.Down = other.LeftStick.Down.Clone();
        LeftStick.Left = other.LeftStick.Left.Clone();
        LeftStick.Right = other.LeftStick.Right.Clone();
        LeftStick.AxisX = other.LeftStick.AxisX.Clone();
        LeftStick.AxisY = other.LeftStick.AxisY.Clone();

        RightStick.Up = other.RightStick.Up.Clone();
        RightStick.Down = other.RightStick.Down.Clone();
        RightStick.Left = other.RightStick.Left.Clone();
        RightStick.Right = other.RightStick.Right.Clone();
        RightStick.AxisX = other.RightStick.AxisX.Clone();
        RightStick.AxisY = other.RightStick.AxisY.Clone();

        LeftTrigger.Digital = other.LeftTrigger.Digital.Clone();
        LeftTrigger.Analog = other.LeftTrigger.Analog.Clone();
        RightTrigger.Digital = other.RightTrigger.Digital.Clone();
        RightTrigger.Analog = other.RightTrigger.Analog.Clone();
    }
}
