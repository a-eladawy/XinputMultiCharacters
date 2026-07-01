namespace XInputMultiCharacter.Models;

public struct XboxState
{
    public bool A, B, X, Y, LB, RB, Back, Start;
    public bool LeftStickClick, RightStickClick;
    public bool DPadUp, DPadDown, DPadLeft, DPadRight;
    public double LeftStickX, LeftStickY;
    public double RightStickX, RightStickY;
    public double LeftTrigger, RightTrigger;
}
