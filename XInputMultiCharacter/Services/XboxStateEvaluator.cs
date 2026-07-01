using System.Windows.Forms;
using Nefarius.ViGEm.Client.Targets;
using Nefarius.ViGEm.Client.Targets.Xbox360;
using SharpDX.DirectInput;
using XInputMultiCharacter.Models;

namespace XInputMultiCharacter.Services;

/// <summary>
/// Pure logic: turns a ControllerProfile + current raw input state into an XboxState,
/// and pushes an XboxState onto a ViGEm virtual controller. No knowledge of "which slot
/// is active" lives here - that's MultiCharacterRuntime's job.
/// </summary>
public static class XboxStateEvaluator
{
    public static XboxState Evaluate(ControllerProfile profile, GlobalHookService hooks, JoystickState? di)
    {
        var state = new XboxState();

        foreach (var kvp in profile.ButtonBindings)
        {
            bool pressed = EvaluateDigital(kvp.Value, hooks, di);
            ApplyButtonToState(kvp.Key, pressed, ref state);
        }

        (state.LeftStickX, state.LeftStickY) = EvaluateStick(profile.LeftStick, hooks, di);
        (state.RightStickX, state.RightStickY) = EvaluateStick(profile.RightStick, hooks, di);
        state.LeftTrigger = EvaluateTrigger(profile.LeftTrigger, hooks, di);
        state.RightTrigger = EvaluateTrigger(profile.RightTrigger, hooks, di);

        return state;
    }

    public static void Apply(IXbox360Controller controller, XboxState s)
    {
        controller.SetButtonState(Xbox360Button.A, s.A);
        controller.SetButtonState(Xbox360Button.B, s.B);
        controller.SetButtonState(Xbox360Button.X, s.X);
        controller.SetButtonState(Xbox360Button.Y, s.Y);
        controller.SetButtonState(Xbox360Button.LeftShoulder, s.LB);
        controller.SetButtonState(Xbox360Button.RightShoulder, s.RB);
        controller.SetButtonState(Xbox360Button.Back, s.Back);
        controller.SetButtonState(Xbox360Button.Start, s.Start);
        controller.SetButtonState(Xbox360Button.LeftThumb, s.LeftStickClick);
        controller.SetButtonState(Xbox360Button.RightThumb, s.RightStickClick);
        controller.SetButtonState(Xbox360Button.Up, s.DPadUp);
        controller.SetButtonState(Xbox360Button.Down, s.DPadDown);
        controller.SetButtonState(Xbox360Button.Left, s.DPadLeft);
        controller.SetButtonState(Xbox360Button.Right, s.DPadRight);

        controller.SetAxisValue(Xbox360Axis.LeftThumbX, ToShort(s.LeftStickX));
        controller.SetAxisValue(Xbox360Axis.LeftThumbY, ToShort(s.LeftStickY));
        controller.SetAxisValue(Xbox360Axis.RightThumbX, ToShort(s.RightStickX));
        controller.SetAxisValue(Xbox360Axis.RightThumbY, ToShort(s.RightStickY));
        controller.SetSliderValue(Xbox360Slider.LeftTrigger, (byte)Math.Clamp(s.LeftTrigger * 255, 0, 255));
        controller.SetSliderValue(Xbox360Slider.RightTrigger, (byte)Math.Clamp(s.RightTrigger * 255, 0, 255));

        controller.SubmitReport();
    }

    private static short ToShort(double v) => (short)Math.Clamp(v * 32767, -32768, 32767);

    private static void ApplyButtonToState(XboxButton b, bool pressed, ref XboxState s)
    {
        switch (b)
        {
            case XboxButton.A: s.A = pressed; break;
            case XboxButton.B: s.B = pressed; break;
            case XboxButton.X: s.X = pressed; break;
            case XboxButton.Y: s.Y = pressed; break;
            case XboxButton.LB: s.LB = pressed; break;
            case XboxButton.RB: s.RB = pressed; break;
            case XboxButton.Back: s.Back = pressed; break;
            case XboxButton.Start: s.Start = pressed; break;
            case XboxButton.LeftStickClick: s.LeftStickClick = pressed; break;
            case XboxButton.RightStickClick: s.RightStickClick = pressed; break;
            case XboxButton.DPadUp: s.DPadUp = pressed; break;
            case XboxButton.DPadDown: s.DPadDown = pressed; break;
            case XboxButton.DPadLeft: s.DPadLeft = pressed; break;
            case XboxButton.DPadRight: s.DPadRight = pressed; break;
        }
    }

    private static bool EvaluateDigital(InputBinding b, GlobalHookService hooks, JoystickState? di) => b.Kind switch
    {
        InputSourceKind.Keyboard => hooks.PressedKeys.Contains((Keys)b.Code),
        InputSourceKind.MouseButton => hooks.PressedMouseButtons.Contains((MouseButtons)b.Code),
        InputSourceKind.DIButton => di != null && b.Code < di.Buttons.Length && di.Buttons[b.Code],
        InputSourceKind.DIPovUp => IsPov(di, 0),
        InputSourceKind.DIPovRight => IsPov(di, 9000),
        InputSourceKind.DIPovDown => IsPov(di, 18000),
        InputSourceKind.DIPovLeft => IsPov(di, 27000),
        _ => false
    };

    private static bool IsPov(JoystickState? di, int target)
    {
        if (di == null || di.PointOfViewControllers.Length == 0) return false;
        int pov = di.PointOfViewControllers[0];
        if (pov < 0) return false;
        int diff = Math.Abs(pov - target);
        return diff < 4500 || diff > 36000 - 4500;
    }

    private static (double x, double y) EvaluateStick(StickBinding sb, GlobalHookService hooks, JoystickState? di)
    {
        double x, y;

        if (sb.AxisX.Kind == InputSourceKind.DIAxis && di != null)
            x = Normalize(GetAxisRaw(di, sb.AxisX.Code)) * (sb.AxisX.Invert ? -1 : 1);
        else
            x = (EvaluateDigital(sb.Right, hooks, di) ? 1 : 0) - (EvaluateDigital(sb.Left, hooks, di) ? 1 : 0);

        if (sb.AxisY.Kind == InputSourceKind.DIAxis && di != null)
            y = Normalize(GetAxisRaw(di, sb.AxisY.Code)) * (sb.AxisY.Invert ? -1 : 1);
        else
            y = (EvaluateDigital(sb.Up, hooks, di) ? 1 : 0) - (EvaluateDigital(sb.Down, hooks, di) ? 1 : 0);

        return (Math.Clamp(x, -1, 1), Math.Clamp(y, -1, 1));
    }

    private static double EvaluateTrigger(TriggerBinding tb, GlobalHookService hooks, JoystickState? di)
    {
        if (tb.Analog.Kind == InputSourceKind.DIAxis && di != null)
        {
            double v = GetAxisRaw(di, tb.Analog.Code) / 65535.0;
            return Math.Clamp(tb.Analog.Invert ? 1 - v : v, 0, 1);
        }
        if (tb.Analog.Kind == InputSourceKind.DISlider && di != null && tb.Analog.Code < di.Sliders.Length)
            return Math.Clamp(di.Sliders[tb.Analog.Code] / 65535.0, 0, 1);

        return EvaluateDigital(tb.Digital, hooks, di) ? 1.0 : 0.0;
    }

    private static double Normalize(int raw) => (raw - 32767) / 32767.0;

    private static int GetAxisRaw(JoystickState di, int code) => code switch
    {
        0 => di.X,
        1 => di.Y,
        2 => di.Z,
        3 => di.RotationX,
        4 => di.RotationY,
        5 => di.RotationZ,
        _ => 32767
    };
}
