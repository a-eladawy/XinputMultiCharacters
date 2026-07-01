using System.Windows.Forms;
using SharpDX.DirectInput;
using XInputMultiCharacter.Models;

namespace XInputMultiCharacter.Services;

/// <summary>
/// The heart of the app. Owns all 6 player slots (each with its own always-connected
/// virtual Xbox 360 controller), listens for global switch hotkeys, and on every tick
/// feeds live input only to the currently-active slot. Whenever the active slot changes,
/// the slot being left behind is immediately reset to a neutral state so it doesn't hold
/// a stuck button or a drifted stick.
/// </summary>
public class MultiCharacterRuntime : IDisposable
{
    public const int SlotCount = 6;

    public PlayerSlot[] Slots { get; } = new PlayerSlot[SlotCount];
    public SharedInputSource Source { get; } = new();

    private readonly GlobalHookService _hooks;
    private readonly DirectInputService _diService;
    private System.Threading.Timer? _timer;
    private int _activeIndex;

    public int ActiveIndex => _activeIndex;

    /// <summary>Fired whenever the active slot changes (new index).</summary>
    public event Action<int>? ActiveChanged;

    /// <summary>Fired every tick for the active slot, and once (with a neutral state) for a slot that just went inactive.</summary>
    public event Action<int, XboxState>? StateUpdated;

    public MultiCharacterRuntime(GlobalHookService hooks, DirectInputService diService)
    {
        _hooks = hooks;
        _diService = diService;

        for (int i = 0; i < SlotCount; i++)
        {
            Slots[i] = new PlayerSlot
            {
                Name = $"Player {i + 1}",
                Profile = ControllerProfile.CreateDefaultKeyboardProfile(),
                SwitchHotkey = new HotkeyBinding { Alt = true, Key = DigitKeyFor(i) }
            };
        }

        _hooks.RawKeyDown += OnRawKeyDown;
    }

    private static Keys DigitKeyFor(int index) => index switch
    {
        0 => Keys.D1,
        1 => Keys.D2,
        2 => Keys.D3,
        3 => Keys.D4,
        4 => Keys.D5,
        5 => Keys.D6,
        _ => Keys.None
    };

    private void OnRawKeyDown(object? sender, KeyEventArgs e)
    {
        for (int i = 0; i < SlotCount; i++)
        {
            if (Slots[i].SwitchHotkey.Matches(_hooks.PressedKeys, e.KeyCode))
            {
                SetActive(i);
                return;
            }
        }
    }

    public void SetActive(int index)
    {
        if (index < 0 || index >= SlotCount || index == _activeIndex) return;
        NeutralizeSlot(_activeIndex);
        _activeIndex = index;
        ActiveChanged?.Invoke(_activeIndex);
    }

    public void ConnectAll(VirtualControllerService vigem)
    {
        foreach (var slot in Slots)
            slot.Controller ??= vigem.CreateController();
    }

    public void DisconnectAll()
    {
        foreach (var slot in Slots)
        {
            slot.Controller?.Disconnect();
            slot.Controller = null;
        }
    }

    public void Start() => _timer ??= new System.Threading.Timer(_ => Tick(), null, 0, 8);

    public void Stop()
    {
        _timer?.Dispose();
        _timer = null;
    }

    private void Tick()
    {
        var slot = Slots[_activeIndex];
        if (slot.Controller == null) return;

        JoystickState? di = Source.Mode == InputDeviceMode.DirectInput && Source.DeviceGuid.HasValue
            ? _diService.Poll(Source.DeviceGuid.Value)
            : null;

        var state = XboxStateEvaluator.Evaluate(slot.Profile, _hooks, di);
        XboxStateEvaluator.Apply(slot.Controller, state);
        StateUpdated?.Invoke(_activeIndex, state);
    }

    private void NeutralizeSlot(int index)
    {
        var slot = Slots[index];
        if (slot.Controller == null) return;
        var neutral = new XboxState();
        XboxStateEvaluator.Apply(slot.Controller, neutral);
        StateUpdated?.Invoke(index, neutral);
    }

    public void Dispose()
    {
        Stop();
        _hooks.RawKeyDown -= OnRawKeyDown;
        DisconnectAll();
    }
}
