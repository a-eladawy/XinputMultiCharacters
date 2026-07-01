using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using XInputMultiCharacter.Models;
using XInputMultiCharacter.Services;
using XInputMultiCharacter.Views;

namespace XInputMultiCharacter;

public partial class MainWindow : Window
{
    private readonly GlobalHookService _hooks = new();
    private readonly DirectInputService _diService = new();
    private VirtualControllerService? _vigem;
    private MultiCharacterRuntime? _runtime;

    private readonly TabItem[] _tabItems = new TabItem[MultiCharacterRuntime.SlotCount];
    private readonly PlayerSlotView[] _views = new PlayerSlotView[MultiCharacterRuntime.SlotCount];
    private bool _connected;

    public MainWindow()
    {
        InitializeComponent();

        try
        {
            _vigem = new VirtualControllerService();
        }
        catch (Exception ex)
        {
            MessageBox.Show(this,
                "Could not connect to the ViGEmBus driver.\n\n" + ex.Message +
                "\n\nInstall it from https://github.com/ViGEm/ViGEmBus/releases and restart this app.",
                "ViGEmBus not found", MessageBoxButton.OK, MessageBoxImage.Warning);
        }

        _runtime = new MultiCharacterRuntime(_hooks, _diService);
        _runtime.ActiveChanged += OnActiveChanged;
        _runtime.StateUpdated += OnStateUpdated;

        ModeCombo.ItemsSource = Enum.GetValues(typeof(InputDeviceMode));
        ModeCombo.SelectedItem = _runtime.Source.Mode;
        UpdateDeviceComboVisibility();
        RefreshDevices_Click(this, new RoutedEventArgs());

        BuildTabs();
        UpdateActiveLabel(0);

        // All 6 controllers are meant to be connected at once - do it automatically on launch.
        ConnectAll_Click(this, new RoutedEventArgs());
        _runtime.Start();
    }

    private void BuildTabs()
    {
        for (int i = 0; i < MultiCharacterRuntime.SlotCount; i++)
        {
            int index = i;
            var slot = _runtime!.Slots[i];
            var view = new PlayerSlotView(slot, _runtime.Source, _hooks, _diService);
            view.NameChanged += name => UpdateTabHeader(index, name);
            view.ActivateRequested += () => _runtime.SetActive(index);
            view.CopyMappingRequested += profile => CopyMappingToAll(index, profile);

            var tab = new TabItem { Content = view };
            _tabItems[i] = tab;
            _views[i] = view;
            Tabs.Items.Add(tab);
            UpdateTabHeader(i, slot.Name);
        }

        _views[0].SetActiveVisual(true);
        Tabs.SelectedIndex = 0;
    }

    private void CopyMappingToAll(int sourceIndex, ControllerProfile sourceProfile)
    {
        for (int i = 0; i < MultiCharacterRuntime.SlotCount; i++)
        {
            if (i == sourceIndex) continue;
            _runtime!.Slots[i].Profile.CopyBindingsFrom(sourceProfile);
            _views[i].RefreshMappingDisplay();
        }
    }

    private void UpdateTabHeader(int index, string name) =>
        _tabItems[index].Header = (index == _runtime!.ActiveIndex ? "\u25B6 " : "") + name;

    private void OnActiveChanged(int newIndex)
    {
        Dispatcher.BeginInvoke(() =>
        {
            for (int i = 0; i < MultiCharacterRuntime.SlotCount; i++)
            {
                _views[i].SetActiveVisual(i == newIndex);
                UpdateTabHeader(i, _runtime!.Slots[i].Name);
            }
            UpdateActiveLabel(newIndex);
        });
    }

    private void UpdateActiveLabel(int index) => ActiveLabel.Text = $"Active: {_runtime!.Slots[index].Name}";

    private void OnStateUpdated(int index, XboxState state) =>
        Dispatcher.BeginInvoke(() => _views[index].DiagramControl.ApplyState(state));

    private void ModeCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_runtime == null) return;
        _runtime.Source.Mode = (InputDeviceMode)ModeCombo.SelectedItem;
        UpdateDeviceComboVisibility();
    }

    private void UpdateDeviceComboVisibility() =>
        DeviceCombo.Visibility = _runtime!.Source.Mode == InputDeviceMode.DirectInput ? Visibility.Visible : Visibility.Collapsed;

    private void RefreshDevices_Click(object sender, RoutedEventArgs e)
    {
        var devices = _diService.GetDevices();
        DeviceCombo.ItemsSource = devices;
        if (_runtime!.Source.DeviceGuid.HasValue)
        {
            var match = devices.Find(d => d.InstanceGuid == _runtime.Source.DeviceGuid.Value);
            if (match != null) DeviceCombo.SelectedItem = match;
        }
        else if (devices.Count > 0)
        {
            DeviceCombo.SelectedIndex = 0;
        }
    }

    private void DeviceCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (DeviceCombo.SelectedItem is DirectInputDeviceInfo info)
        {
            _runtime!.Source.DeviceGuid = info.InstanceGuid;
            var handle = new System.Windows.Interop.WindowInteropHelper(this).Handle;
            if (handle != IntPtr.Zero) _diService.OpenDevice(info.InstanceGuid, handle);
        }
    }

    private void ConnectAll_Click(object sender, RoutedEventArgs e)
    {
        if (!_connected)
        {
            if (_vigem == null)
            {
                MessageBox.Show(this, "ViGEmBus driver is not available. Install it and restart the app.", "Error");
                return;
            }
            _runtime!.ConnectAll(_vigem);
            _connected = true;
            ConnectButton.Content = "Disconnect All";
        }
        else
        {
            _runtime!.DisconnectAll();
            _connected = false;
            ConnectButton.Content = "Connect All";
        }
    }

    protected override void OnClosed(EventArgs e)
    {
        _runtime?.Dispose();
        _hooks.Dispose();
        _diService.Dispose();
        _vigem?.Dispose();
        base.OnClosed(e);
    }
}
