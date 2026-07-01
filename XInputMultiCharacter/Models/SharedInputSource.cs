namespace XInputMultiCharacter.Models;

/// <summary>The single physical device (keyboard+mouse OR one DirectInput device) driving every player slot.</summary>
public class SharedInputSource
{
    public InputDeviceMode Mode { get; set; } = InputDeviceMode.KeyboardMouse;
    public Guid? DeviceGuid { get; set; }
}
