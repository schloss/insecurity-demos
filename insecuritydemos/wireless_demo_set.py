import json
import wlan
import wx
from ObjectListView import ObjectListView, ColumnDefn
from demos import wireless_demos
from tshark import TShark
from Queue import Empty

class WirelessDemoSet():
    """A collection of wireless insecurity demos."""

    # Class constants.
    DEMOS = (wireless_demos.AccessPointDemo(),)
    BORDER = 5
    REFRESH_LABEL = "Refresh"
    NETWORK_INTERFACE_LABEL = "Network Interface"
    WIRELESS_NETWORK_LABEL = "Wireless Network"
    MONITOR_MODE_LABEL_OFF = "Monitor mode is OFF."
    TSHARK_SEPARATOR = ','
    TSHARK_POLL_INTERVAL = 500

    def __init__(self, parent):
        self._polling_demo = None
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self._poll_tshark)
        self.tshark = None
        self.interfaces = []
        self._init_control_panel(parent)
        self._init_data_panel(parent)

    def get_users(self):
        return self.data_grid.GetObjects()

    def initialize_data(self):
        self.wireless_refresh()

    def merge_users(self, new_users):
        users_dict = {}
        users = self.get_users()
        for user in users:
            users_dict[user.mac] = user
        for new_user in new_users:
            user = users_dict.get(new_user.mac)
            if user:
                user.merge(new_user)
            else:
                user = new_user
                users_dict[user.mac] = user
        self.data_grid.SetObjects(users_dict.values())

    def destroy(self):
        for i in self.interfaces:
            if i.monitor_mode:
                i.disable_monitor_mode()

    def _poll_tshark(self, event):
        while self.tshark:
            try:
                line = self.tshark.queue.get_nowait()
            except Empty:
                break
            line = line.strip()
            raw_fields = line.split(self.TSHARK_SEPARATOR)
            fields = self._polling_demo.interpret_tshark_output(raw_fields)
            if fields:
                print fields
                new_user = wlan.User(**fields)
                for user in self.get_users():
                    if user.mac == new_user.mac:
                        old_user = user
                        break
                else:
                    old_user = None
                if old_user:
                    old_user.merge(new_user)
                    self.data_grid.RefreshObject(old_user)
                else:
                    self.data_grid.AddObject(new_user)

    def demo_names(self):
        return [demo.TITLE for demo in self.DEMOS]

    def select_demo(self, demo):
        demo = self._get_demo(demo)
        if demo:
            self._enable_network_panel(demo.WIRELESS_NETWORKS_CONTROL)
            self._enable_interface_panel(True)
        else:
            self._enable_network_panel(False)
            self._enable_interface_panel(False)

    def enable_demo(self, demo_title, is_enabled):
        demo = self._get_demo(demo_title)
        if not demo:
            return
        self._enable_network_panel(not is_enabled and
                                   demo.WIRELESS_NETWORKS_CONTROL)
        self._enable_interface_panel(not is_enabled)
        wx.CallAfter(self._enable_demo, demo, is_enabled)

    def _enable_demo(self, demo, is_enabled):
        if not is_enabled:
            self.timer.Stop()
            self.tshark.stop_capture()
            self.tshark = None
            self._polling_demo = None
            return
        # Put the interface into the correct mode.
        interface = self._get_interface()
        if demo.MONITOR_MODE and not interface.monitor_mode:
            interface.enable_monitor_mode()
            self.wireless_refresh()
        elif not demo.MONITOR_MODE and interface.monitor_mode:
            interface.disable_monitor_mode()
            self.wireless_refresh()
        # Start TShark with the demo parameters.
        self._polling_demo = demo
        interface = self._get_interface()
        interface = interface.monitor_mode or interface.interface_name
        self.tshark = TShark(interface=interface,
                             fields=demo.TSHARK_FIELDS,
                             separator=self.TSHARK_SEPARATOR,
                             read_filter=demo.TSHARK_READ_FILTER)
        self.tshark.start_capture()
        self.timer.Start(self.TSHARK_POLL_INTERVAL)

    def _enable_network_panel(self, is_enabled):
        for control in (self.network_choice, self.network_refresh_button):
            control.Enable(is_enabled)

    def _enable_interface_panel(self, is_enabled):
        for control in (self.monitor_mode_label,
                        self.interface_choice,
                        self.interface_refresh_button):
            control.Enable(is_enabled)


    def _get_demo(self, title):
        for demo in self.DEMOS:
            if demo.TITLE == title:
                return demo
        return None

    def _get_interface(self):
        name = self.interface_choice.GetStringSelection()
        for i in self.interfaces:
            if i.interface_name == name:
                return i
        return None

    def _init_control_panel(self, parent):
        self.control_panel = wx.Panel(parent, -1)

        # Network interface selection.
        self.interface_choice = wx.Choice(self.control_panel, -1,
                                          size=wx.Size(100, -1),
                                          choices=[])
        self.interface_choice.Bind(wx.EVT_CHOICE,
                                   self._interface_selected)
        self.interface_refresh_button = wx.Button(self.control_panel,
                                                  label=self.REFRESH_LABEL)
        self.interface_refresh_button.Bind(wx.EVT_BUTTON,
                                           self.wireless_refresh)
        self.monitor_mode_label = wx.StaticText(self.control_panel, -1,
                                                self.MONITOR_MODE_LABEL_OFF)

        # Wireless network selection.
        self.network_choice = wx.Choice(self.control_panel, -1,
                                        size=wx.Size(300, -1),
                                        choices=[])
        self.network_refresh_button = wx.Button(self.control_panel,
                                                label=self.REFRESH_LABEL)
        self.network_refresh_button.Bind(wx.EVT_BUTTON, self.network_refresh)

        # Layout.
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALL | wx.ALIGN_CENTER_VERTICAL

        self.interface_box = wx.StaticBox(self.control_panel, -1,
                                           self.NETWORK_INTERFACE_LABEL)
        interface_sizer = wx.StaticBoxSizer(self.interface_box, wx.HORIZONTAL)
        interface_sizer.Add(self.monitor_mode_label,
                            flag=flags,
                            border=self.BORDER)
        interface_sizer.Add(self.interface_choice,
                            flag=flags,
                            border=self.BORDER)
        interface_sizer.Add(self.interface_refresh_button,
                            flag=flags,
                            border=self.BORDER)
        sizer.Add(interface_sizer, flag=flags, border=self.BORDER)

        self.network_box = wx.StaticBox(self.control_panel, -1,
                                         self.WIRELESS_NETWORK_LABEL)
        network_sizer = wx.StaticBoxSizer(self.network_box, wx.HORIZONTAL)
        network_sizer.Add(self.network_choice,
                          flag=flags,
                          border=self.BORDER)
        network_sizer.Add(self.network_refresh_button,
                          flag=flags,
                          border=self.BORDER)
        sizer.Add(network_sizer, flag=flags, border=self.BORDER)
        self.control_panel.SetSizer(sizer)

    def _init_data_panel(self, parent):
        self.data_panel = wx.Panel(parent, -1, style=0)
        self.data_grid = ObjectListView(self.data_panel,
                                        wx.ID_ANY,
                                        size=(-1,600),
                                        style=(wx.LC_REPORT |
                                               wx.LC_VRULES |
                                               wx.SUNKEN_BORDER))
        cols = [ColumnDefn("MAC Address", "left", 175, "mac",
                           isEditable=False),
                ColumnDefn("Nickname", "left", 175,
                           valueGetter="nickname_to_string",
                           valueSetter="nickname_from_string"),
                ColumnDefn("Wifi Card", "left", 175, "hardware",
                           isEditable=False),
                ColumnDefn("IP Address", "left", 175, "ip",
                           isEditable=False),
                ColumnDefn("Wifi Networks Previously Used", "left", 175,
                           valueGetter="aps_to_string",
                           isEditable=False,
                           minimumWidth=175,
                           isSpaceFilling=True,
                           checkStateGetter="anonymous")]
        self.data_grid.SetColumns(cols)
        self.data_grid.SetEmptyListMsg("Start a demo or use \"File > Import\""
                                       " to populate this list.")
        self.data_grid.cellEditMode = ObjectListView.CELLEDIT_DOUBLECLICK
        font = wx.Font(pointSize=11,
                       family=wx.FONTFAMILY_MODERN,
                       style=wx.FONTSTYLE_NORMAL,
                       weight=wx.FONTWEIGHT_NORMAL,
                       underline=False,
                       face="",
                       encoding=wx.FONTENCODING_DEFAULT)
        self.data_grid.SetFont(font)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.data_grid, 1, wx.ALL|wx.EXPAND, self.BORDER)
        self.data_panel.SetSizer(sizer)
        self.data_grid.Bind(wx.EVT_LIST_ITEM_SELECTED, self._item_selected)
        self.data_grid.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._item_deselected)

    def _item_selected(self, event):
        user = self.data_grid.GetSelectedObject()
        ui = event.GetEventObject()
        if user:
            ui.SetToolTipString(user.aps_to_string('\n'))
        else:
            ui.SetToolTip(None)
        event.Skip()

    def _item_deselected(self, event):
        event.GetEventObject().SetToolTip(None)
        event.Skip()

    def wireless_refresh(self, event=None):
        current_interface = self.interface_choice.GetStringSelection()
        new_interfaces = wlan.enumerate_interfaces()

        # Retain knowledge of which interfaces are in monitor
        # mode. This is needed because airmon-ng only reports the
        # monitor mode name of an inteface in the results of putting
        # that interface into monitor mode, but not when listing all
        # interfaces in general. The assumption here is that no
        # external program or action will change the monitor mode
        # state of an interface.
        for new in new_interfaces:
            for old in self.interfaces:
                if new.interface_name == old.interface_name:
                    new.monitor_mode = old.monitor_mode

        # Don't list monitoring interfaces as separate interfaces.
        for i in new_interfaces:
            name = i.interface_name
            for j in new_interfaces:
                if name == j.monitor_mode:
                    new_interfaces.remove(i)

        self.interfaces = new_interfaces

        # Construct a list of the new interface names, taking care to
        # track changes in monitor mode.
        interface_names = []
        for i in self.interfaces:
            if i.interface_name == current_interface:
                current_interface = i.interface_name
            interface_names.append(i.interface_name)
        self.interface_choice.SetItems(interface_names)
        if current_interface in interface_names:
            self.interface_choice.SetStringSelection(current_interface)
        else:
            self.interface_choice.SetSelection(0)

        self._interface_selected()

    def _interface_selected(self, event=None):
        # Show the user the state of monitor mode.
        interface = self._get_interface()
        if interface and interface.monitor_mode:
            label = "Monitoring as %s." % interface.monitor_mode
        else:
            label = self.MONITOR_MODE_LABEL_OFF
        self.monitor_mode_label.SetLabel(label)

    def network_refresh(self, event=None):
        interface = self.interface_choice.GetStringSelection()
        if not interface:
            self.network_choice.SetItems([])
        else:
            current_network = self.network_choice.GetStringSelection()
            networks = wlan.enumerate_networks(interface)
            network_names = map(str, networks)
            self.network_choice.SetItems(network_names)
            if network_names:
                if current_network in network_names:
                    self.network_choice.SetStringSelection(current_network)
                else:
                    self.network_choice.SetSelection(0)
