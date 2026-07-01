using System.Windows.Forms;

namespace XInputMultiCharacter.Models;

public class InputBinding
{
    public InputSourceKind Kind { get; set; } = InputSourceKind.None;
    public int Code { get; set; }
    public bool Invert { get; set; }

    public InputBinding Clone() => new() { Kind = Kind, Code = Code, Invert = Invert };

    public override string ToString() => Kind switch
    {
        InputSourceKind.None => "Unbound",
        InputSourceKind.Keyboard => ((Keys)Code).ToString(),
        InputSourceKind.MouseButton => "Mouse " + (MouseButtons)Code,
        InputSourceKind.DIButton => $"Btn {Code + 1}",
        InputSourceKind.DIPovUp => "D-Pad Up (device)",
        InputSourceKind.DIPovDown => "D-Pad Down (device)",
        InputSourceKind.DIPovLeft => "D-Pad Left (device)",
        InputSourceKind.DIPovRight => "D-Pad Right (device)",
        InputSourceKind.DIAxis => $"Axis {Code}" + (Invert ? " (inv)" : ""),
        InputSourceKind.DISlider => $"Slider {Code}",
        _ => "?"
    };
}
