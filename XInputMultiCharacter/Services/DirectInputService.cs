using SharpDX.DirectInput;

namespace XInputMultiCharacter.Services;

public class DirectInputDeviceInfo
{
    public Guid InstanceGuid { get; set; }
    public string Name { get; set; } = "";
    public override string ToString() => Name;
}

/// <summary>Enumerates and polls DirectInput gamepads/joysticks.</summary>
public class DirectInputService : IDisposable
{
    private readonly DirectInput _directInput = new();
    private readonly Dictionary<Guid, Joystick> _openDevices = new();

    public List<DirectInputDeviceInfo> GetDevices()
    {
        var list = new List<DirectInputDeviceInfo>();

        foreach (var d in _directInput.GetDevices(SharpDX.DirectInput.DeviceType.Gamepad, DeviceEnumerationFlags.AllDevices))
            list.Add(new DirectInputDeviceInfo { InstanceGuid = d.InstanceGuid, Name = d.InstanceName });

        foreach (var d in _directInput.GetDevices(SharpDX.DirectInput.DeviceType.Joystick, DeviceEnumerationFlags.AllDevices))
            if (!list.Exists(x => x.InstanceGuid == d.InstanceGuid))
                list.Add(new DirectInputDeviceInfo { InstanceGuid = d.InstanceGuid, Name = d.InstanceName });

        return list;
    }

    public void OpenDevice(Guid instanceGuid, IntPtr windowHandle)
    {
        if (_openDevices.ContainsKey(instanceGuid) || windowHandle == IntPtr.Zero) return;

        var joystick = new Joystick(_directInput, instanceGuid);
        joystick.SetCooperativeLevel(windowHandle, CooperativeLevel.NonExclusive | CooperativeLevel.Background);
        joystick.Acquire();
        _openDevices[instanceGuid] = joystick;
    }

    public JoystickState? Poll(Guid instanceGuid)
    {
        if (!_openDevices.TryGetValue(instanceGuid, out var joystick)) return null;
        try
        {
            joystick.Poll();
            return joystick.GetCurrentState();
        }
        catch
        {
            try { joystick.Acquire(); } catch { /* ignore */ }
            return null;
        }
    }

    public void Dispose()
    {
        foreach (var j in _openDevices.Values)
        {
            try { j.Unacquire(); j.Dispose(); } catch { /* ignore */ }
        }
        _directInput.Dispose();
    }
}
