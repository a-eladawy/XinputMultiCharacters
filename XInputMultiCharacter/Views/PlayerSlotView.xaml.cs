using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using XInputMultiCharacter.Models;
using XInputMultiCharacter.Services;

namespace XInputMultiCharacter.Views;

public partial class PlayerSlotView : UserControl
{
    private readonly PlayerSlot _slot;
    private readonly SharedInputSource _source;
    private readonly GlobalHookService _hooks;
    private readonly DirectInputService _diService;

    /// <summary>Raised when the user renames this slot (new name).</summary>
    public event Action<string>? NameChanged;

    /// <summary>Raised when the user clicks "Make Active Now".</summary>
    public event Action? ActivateRequested;

    /// <summary>Raised when the user clicks "Copy Mapping To All Players".</summary>
    public event Action<ControllerProfile>? CopyMappingRequested;

    public XboxControllerDiagram DiagramControl => Diagram;

    public PlayerSlotView(PlayerSlot slot, SharedInputSource source, GlobalHookService hooks, DirectInputService diService)
    {
        InitializeComponent();
        _slot = slot;
        _source = source;
        _hooks = hooks;
        _diService = diService;

        NameBox.Text = _slot.Name;
        HotkeyText.Text = _slot.SwitchHotkey.ToString();

        BuildMappingRows();
    }

    public void SetActiveVisual(bool isActive) => ActiveBadge.Visibility = isActive ? Visibility.Visible : Visibility.Collapsed;

    private void NameBox_TextChanged(object sender, TextChangedEventArgs e)
    {
        _slot.Name = string.IsNullOrWhiteSpace(NameBox.Text) ? _slot.Name : NameBox.Text;
        NameChanged?.Invoke(_slot.Name);
    }

    private void Activate_Click(object sender, RoutedEventArgs e) => ActivateRequested?.Invoke();

    private void CopyToAll_Click(object sender, RoutedEventArgs e) => CopyMappingRequested?.Invoke(_slot.Profile);

    /// <summary>Called by MainWindow after a "copy mapping" from another slot lands on this one.</summary>
    public void RefreshMappingDisplay() => BuildMappingRows();

    private async void SetHotkey_Click(object sender, RoutedEventArgs e)
    {
        var button = (Button)sender;
        button.Content = "...";
        button.IsEnabled = false;

        var captured = await CaptureHotkeyAsync();
        if (captured != null)
        {
            _slot.SwitchHotkey = captured;
            HotkeyText.Text = captured.ToString();
        }

        button.Content = "Set";
        button.IsEnabled = true;
    }

    private Task<HotkeyBinding?> CaptureHotkeyAsync()
    {
        var tcs = new TaskCompletionSource<HotkeyBinding?>();

        void Handler(object? s, System.Windows.Forms.KeyEventArgs e)
        {
            if (HotkeyBinding.IsModifierKey(e.KeyCode)) return; // wait for the "real" key, not just Alt/Ctrl/Shift alone
            tcs.TrySetResult(new HotkeyBinding
            {
                Key = e.KeyCode,
                Alt = _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.LMenu) || _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.RMenu) || _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.Menu),
                Ctrl = _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.LControlKey) || _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.RControlKey) || _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.ControlKey),
                Shift = _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.LShiftKey) || _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.RShiftKey) || _hooks.PressedKeys.Contains(System.Windows.Forms.Keys.ShiftKey)
            });
        }

        _hooks.RawKeyDown += Handler;
        _ = Task.Delay(6000).ContinueWith(_ => tcs.TrySetResult(null));

        return tcs.Task.ContinueWith(t =>
        {
            _hooks.RawKeyDown -= Handler;
            return t.Result;
        }, TaskScheduler.FromCurrentSynchronizationContext());
    }

    // ---------------- Input mapping rows (same idea as the single-device version) ----------------

    private void BuildMappingRows()
    {
        MappingsPanel.Children.Clear();

        AddHeader("Buttons");
        foreach (XboxButton b in Enum.GetValues(typeof(XboxButton)))
        {
            var button = b;
            AddButtonRow(button.ToString(),
                () => _slot.Profile.ButtonBindings.TryGetValue(button, out var v) ? v : new InputBinding(),
                v => _slot.Profile.ButtonBindings[button] = v);
        }

        AddHeader("Left Stick");
        AddButtonRow("Up", () => _slot.Profile.LeftStick.Up, v => _slot.Profile.LeftStick.Up = v);
        AddButtonRow("Down", () => _slot.Profile.LeftStick.Down, v => _slot.Profile.LeftStick.Down = v);
        AddButtonRow("Left", () => _slot.Profile.LeftStick.Left, v => _slot.Profile.LeftStick.Left = v);
        AddButtonRow("Right", () => _slot.Profile.LeftStick.Right, v => _slot.Profile.LeftStick.Right = v);
        AddAxisRow("Analog X (overrides L/R)", () => _slot.Profile.LeftStick.AxisX, v => _slot.Profile.LeftStick.AxisX = v);
        AddAxisRow("Analog Y (overrides U/D)", () => _slot.Profile.LeftStick.AxisY, v => _slot.Profile.LeftStick.AxisY = v);

        AddHeader("Right Stick");
        AddButtonRow("Up", () => _slot.Profile.RightStick.Up, v => _slot.Profile.RightStick.Up = v);
        AddButtonRow("Down", () => _slot.Profile.RightStick.Down, v => _slot.Profile.RightStick.Down = v);
        AddButtonRow("Left", () => _slot.Profile.RightStick.Left, v => _slot.Profile.RightStick.Left = v);
        AddButtonRow("Right", () => _slot.Profile.RightStick.Right, v => _slot.Profile.RightStick.Right = v);
        AddAxisRow("Analog X (overrides L/R)", () => _slot.Profile.RightStick.AxisX, v => _slot.Profile.RightStick.AxisX = v);
        AddAxisRow("Analog Y (overrides U/D)", () => _slot.Profile.RightStick.AxisY, v => _slot.Profile.RightStick.AxisY = v);

        AddHeader("Triggers");
        AddButtonRow("Left Trigger (digital)", () => _slot.Profile.LeftTrigger.Digital, v => _slot.Profile.LeftTrigger.Digital = v);
        AddAxisRow("Left Trigger (analog)", () => _slot.Profile.LeftTrigger.Analog, v => _slot.Profile.LeftTrigger.Analog = v);
        AddButtonRow("Right Trigger (digital)", () => _slot.Profile.RightTrigger.Digital, v => _slot.Profile.RightTrigger.Digital = v);
        AddAxisRow("Right Trigger (analog)", () => _slot.Profile.RightTrigger.Analog, v => _slot.Profile.RightTrigger.Analog = v);
    }

    private void AddHeader(string text) => MappingsPanel.Children.Add(new TextBlock
    {
        Text = text,
        FontWeight = FontWeights.Bold,
        Margin = new Thickness(0, 10, 0, 4),
        Foreground = Brushes.White
    });

    private void AddButtonRow(string label, Func<InputBinding> getter, Action<InputBinding> setter)
        => AddRow(label, getter, setter, allowAxis: false);

    private void AddAxisRow(string label, Func<InputBinding> getter, Action<InputBinding> setter)
        => AddRow(label, getter, setter, allowAxis: true);

    private void AddRow(string label, Func<InputBinding> getter, Action<InputBinding> setter, bool allowAxis)
    {
        var panel = new DockPanel { Margin = new Thickness(0, 2, 0, 2) };
        var lbl = new TextBlock { Text = label, Width = 190, Foreground = Brushes.LightGray, VerticalAlignment = VerticalAlignment.Center };
        var valueText = new TextBlock { Width = 130, Foreground = Brushes.Yellow, VerticalAlignment = VerticalAlignment.Center, Text = getter().ToString() };
        var setBtn = new Button { Content = "Set", Width = 50, Margin = new Thickness(4, 0, 4, 0) };
        var clearBtn = new Button { Content = "Clear", Width = 50 };

        setBtn.Click += async (_, _) =>
        {
            setBtn.Content = "...";
            setBtn.IsEnabled = false;
            var captured = await CaptureInputAsync(allowAxis);
            if (captured != null)
            {
                setter(captured);
                valueText.Text = captured.ToString();
            }
            setBtn.Content = "Set";
            setBtn.IsEnabled = true;
        };
        clearBtn.Click += (_, _) => { setter(new InputBinding()); valueText.Text = "Unbound"; };

        DockPanel.SetDock(lbl, Dock.Left);
        DockPanel.SetDock(clearBtn, Dock.Right);
        DockPanel.SetDock(setBtn, Dock.Right);
        panel.Children.Add(lbl);
        panel.Children.Add(clearBtn);
        panel.Children.Add(setBtn);
        panel.Children.Add(valueText);
        MappingsPanel.Children.Add(panel);
    }

    /// <summary>
    /// Captures the next input on the app-wide SHARED source (not a per-slot source, since
    /// this whole app is "one device -> many characters").
    /// </summary>
    private Task<InputBinding?> CaptureInputAsync(bool allowAxis)
    {
        var tcs = new TaskCompletionSource<InputBinding?>();

        void KeyHandler(object? s, System.Windows.Forms.KeyEventArgs e) =>
            tcs.TrySetResult(new InputBinding { Kind = InputSourceKind.Keyboard, Code = (int)e.KeyCode });

        void MouseHandler(object? s, System.Windows.Forms.MouseEventArgs e) =>
            tcs.TrySetResult(new InputBinding { Kind = InputSourceKind.MouseButton, Code = (int)e.Button });

        System.Threading.Timer? poller = null;

        if (_source.Mode == InputDeviceMode.KeyboardMouse)
        {
            _hooks.RawKeyDown += KeyHandler;
            _hooks.RawMouseDown += MouseHandler;
        }
        else if (_source.DeviceGuid.HasValue)
        {
            var guid = _source.DeviceGuid.Value;
            var baseline = _diService.Poll(guid);

            poller = new System.Threading.Timer(_ =>
            {
                if (tcs.Task.IsCompleted) return;
                var state = _diService.Poll(guid);
                if (state == null || baseline == null) return;

                for (int i = 0; i < state.Buttons.Length; i++)
                    if (state.Buttons[i] && (i >= baseline.Buttons.Length || !baseline.Buttons[i]))
                    { tcs.TrySetResult(new InputBinding { Kind = InputSourceKind.DIButton, Code = i }); return; }

                if (state.PointOfViewControllers.Length > 0 && state.PointOfViewControllers[0] != -1)
                {
                    int pov = state.PointOfViewControllers[0];
                    InputSourceKind? dir = pov switch
                    {
                        0 => InputSourceKind.DIPovUp,
                        9000 => InputSourceKind.DIPovRight,
                        18000 => InputSourceKind.DIPovDown,
                        27000 => InputSourceKind.DIPovLeft,
                        _ => null
                    };
                    if (dir.HasValue) { tcs.TrySetResult(new InputBinding { Kind = dir.Value }); return; }
                }

                if (allowAxis)
                {
                    int[] axes = { state.X, state.Y, state.Z, state.RotationX, state.RotationY, state.RotationZ };
                    int[] baseAxes = { baseline.X, baseline.Y, baseline.Z, baseline.RotationX, baseline.RotationY, baseline.RotationZ };
                    for (int i = 0; i < axes.Length; i++)
                        if (Math.Abs(axes[i] - baseAxes[i]) > 10000)
                        { tcs.TrySetResult(new InputBinding { Kind = InputSourceKind.DIAxis, Code = i }); return; }

                    for (int i = 0; i < state.Sliders.Length && i < baseline.Sliders.Length; i++)
                        if (Math.Abs(state.Sliders[i] - baseline.Sliders[i]) > 10000)
                        { tcs.TrySetResult(new InputBinding { Kind = InputSourceKind.DISlider, Code = i }); return; }
                }
            }, null, 0, 20);
        }

        _ = Task.Delay(6000).ContinueWith(_ => tcs.TrySetResult(null));

        return tcs.Task.ContinueWith(t =>
        {
            if (_source.Mode == InputDeviceMode.KeyboardMouse)
            {
                _hooks.RawKeyDown -= KeyHandler;
                _hooks.RawMouseDown -= MouseHandler;
            }
            poller?.Dispose();
            return t.Result;
        }, TaskScheduler.FromCurrentSynchronizationContext());
    }
}
