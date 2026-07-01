using Nefarius.ViGEm.Client;
using Nefarius.ViGEm.Client.Targets;

namespace XInputMultiCharacter.Services;

/// <summary>
/// Wraps the ViGEmBus client connection. Requires the ViGEmBus driver:
/// https://github.com/ViGEm/ViGEmBus/releases
/// </summary>
public sealed class VirtualControllerService : IDisposable
{
    private readonly ViGEmClient _client;

    public VirtualControllerService()
    {
        _client = new ViGEmClient();
    }

    public IXbox360Controller CreateController()
    {
        var controller = _client.CreateXbox360Controller();
        controller.Connect();
        return controller;
    }

    public void Dispose() => _client.Dispose();
}
