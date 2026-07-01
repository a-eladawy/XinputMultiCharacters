using Nefarius.ViGEm.Client.Targets;

namespace XInputMultiCharacter.Models;

/// <summary>One of the 6 virtual characters/controllers. Always connected; "active" ones receive live input.</summary>
public class PlayerSlot
{
    public string Name { get; set; } = "Player";
    public ControllerProfile Profile { get; set; } = ControllerProfile.CreateDefaultKeyboardProfile();
    public HotkeyBinding SwitchHotkey { get; set; } = new();
    public IXbox360Controller? Controller { get; set; }
}
