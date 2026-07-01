namespace XInputMultiCharacter.Models;

public enum XboxButton
{
    A, B, X, Y,
    LB, RB,
    Back, Start, Guide,
    LeftStickClick, RightStickClick,
    DPadUp, DPadDown, DPadLeft, DPadRight
}

public enum InputDeviceMode
{
    KeyboardMouse,
    DirectInput
}

public enum InputSourceKind
{
    None,
    Keyboard,
    MouseButton,
    DIButton,
    DIPovUp,
    DIPovDown,
    DIPovLeft,
    DIPovRight,
    DIAxis,
    DISlider
}
