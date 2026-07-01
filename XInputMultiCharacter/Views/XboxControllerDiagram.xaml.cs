using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using XInputMultiCharacter.Models;

namespace XInputMultiCharacter.Views;

public partial class XboxControllerDiagram : UserControl
{
    private static readonly Brush Pressed = new SolidColorBrush(Color.FromRgb(0xFF, 0xE0, 0x66));
    private readonly Dictionary<Shape, Brush> _defaults = new();

    public XboxControllerDiagram()
    {
        InitializeComponent();
        foreach (var shape in new Shape[]
                 {
                     BtnA, BtnB, BtnX, BtnY, BtnLB, BtnRB, BtnBack, BtnStart,
                     DPadUp, DPadDown, DPadLeft, DPadRight, LeftStickCap, RightStickCap
                 })
        {
            _defaults[shape] = shape.Fill;
        }
    }

    public void ApplyState(XboxState s)
    {
        SetPressed(BtnA, s.A);
        SetPressed(BtnB, s.B);
        SetPressed(BtnX, s.X);
        SetPressed(BtnY, s.Y);
        SetPressed(BtnLB, s.LB);
        SetPressed(BtnRB, s.RB);
        SetPressed(BtnBack, s.Back);
        SetPressed(BtnStart, s.Start);
        SetPressed(DPadUp, s.DPadUp);
        SetPressed(DPadDown, s.DPadDown);
        SetPressed(DPadLeft, s.DPadLeft);
        SetPressed(DPadRight, s.DPadRight);
        SetPressed(LeftStickCap, s.LeftStickClick);
        SetPressed(RightStickCap, s.RightStickClick);

        Canvas.SetLeft(LeftStickCap, 67 + s.LeftStickX * 15);
        Canvas.SetTop(LeftStickCap, 82 - s.LeftStickY * 15);
        Canvas.SetLeft(RightStickCap, 212 + s.RightStickX * 15);
        Canvas.SetTop(RightStickCap, 142 - s.RightStickY * 15);

        double ltH = Math.Clamp(s.LeftTrigger, 0, 1) * 24;
        TriggerLT.Height = ltH;
        Canvas.SetTop(TriggerLT, 32 + (24 - ltH));

        double rtH = Math.Clamp(s.RightTrigger, 0, 1) * 24;
        TriggerRT.Height = rtH;
        Canvas.SetTop(TriggerRT, 32 + (24 - rtH));
    }

    private void SetPressed(Shape shape, bool pressed) => shape.Fill = pressed ? Pressed : _defaults[shape];
}
