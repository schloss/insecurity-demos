import json
import wlan
import wx
import wx.lib.mixins.listctrl as listmixins

TEST_USERS ="""
{"Users": [{"nickname" : "Alice",
            "mac" : "84:3a:4b:0a:0e:14",
            "hardware" : "Intel",
            "ip" : "192.168.2.107"},
           {"nickname" : "Bob",
            "mac" : "14:9d:01:06:e2:cd",
            "hardware" : "Macintosh",
            "ip" : "192.168.2.102",
            "aps" : ["sgnast"]},
           {"nickname" : "Carol",
            "mac" : "07:a1:18:ff:39:32",
            "hardware" : "Atheros"},
           {"mac" : "07:a1:18:ff:01:21",
            "hardware" : "Atheros",
            "aps" : ["LibyanEmbassyWifi2012",
                     "att_starbucks39432",
                     "54-CANARY-ST"]}
            ]
}
"""

class WirelessDemo():
    """A collection of wireless insecurity demos."""

    # Class constants.
    DEMOS = ('Wifi History', 'Pages Visited')
    BORDER = 5
    REFRESH_LABEL = "Refresh"
    NETWORK_INTERFACE_LABEL = "Network Interface"
    WIRELESS_NETWORK_LABEL = "Wireless Network"
    DATA_COLUMN_LABELS = ['MAC Address',
                          'Nickname',
                          'Wifi Card',
                          'IP Address',
                          'Wifi Networks Previously Used']

    def __init__(self, parent):
        self._init_control_panel(parent)
        self._init_data_panel(parent)

    def initialize_data(self):
        self.wireless_refresh()

    def _get_test_users(self):
        data = json.loads(TEST_USERS)
        return [wlan.User(**x) for x in data['Users']]

    def enable_demo(self, demo, is_enabled):
        if not is_enabled:
            return
        for user in self._get_test_users():
            self.data_grid.SetItem(user)

    def enable_control_panel(self, is_enabled):
        for control in (self.interface_choice,
                        self.interface_refresh_button,
                        self.network_choice,
                        self.network_refresh_button):
            control.Enable(is_enabled)

    def _init_control_panel(self, parent):
        self.control_panel = wx.Panel(parent, -1)

        # Network interface selection.
        self.interface_choice = wx.Choice(self.control_panel, -1,
                                          size=wx.Size(200, -1),
                                          choices=[])
        self.interface_refresh_button = wx.Button(self.control_panel,
                                                  label=self.REFRESH_LABEL)
        self.interface_refresh_button.Bind(wx.EVT_BUTTON,
                                           self.wireless_refresh)

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
        self.data_grid = WirelessDataList(self.data_panel,
                                          -1,
                                          size=wx.Size(-1, 400),
                                          style=(wx.LC_REPORT |
                                                 wx.LC_VRULES |
                                                 wx.SUNKEN_BORDER))

        for i, label in enumerate(self.DATA_COLUMN_LABELS):
            self.data_grid.InsertColumn(i, label)
            self.data_grid.SetColumnWidth(i, 175)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.data_grid, 1, wx.EXPAND, self.BORDER)
        self.data_panel.SetSizer(sizer)

    def wireless_refresh(self, event=None):
        current_interface = self.interface_choice.GetStringSelection()
        interfaces = wlan.enumerate_interfaces()
        interface_names = [i.interface_name for i in interfaces]
        self.interface_choice.SetItems(interface_names)
        if interface_names:
            if current_interface in interface_names:
                self.interface_choice.SetStringSelection(current_interface)
            else:
                self.interface_choice.SetSelection(0)

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

class WirelessDataList(wx.ListCtrl,
                       listmixins.ListCtrlAutoWidthMixin,
                       listmixins.TextEditMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        font = wx.Font(pointSize=11,
                       family=wx.FONTFAMILY_MODERN,
                       style=wx.FONTSTYLE_NORMAL,
                       weight=wx.FONTWEIGHT_NORMAL,
                       underline=False,
                       face="",
                       encoding=wx.FONTENCODING_DEFAULT)
        self.SetFont(font)
        listmixins.ListCtrlAutoWidthMixin.__init__(self)
        listmixins.TextEditMixin.__init__(self)

    def SetItem(self, data):
        if isinstance(data, wlan.User):
            i = self.FindItem(-1, data.mac)
            if i < 0:
                i = self.InsertStringItem(0, data.mac)
            if i < 0:
                return
            if data.nickname:
                self.SetStringItem(i, 1, data.nickname)
            if data.hardware:
                self.SetStringItem(i, 2, data.hardware)
            if data.ip:
                self.SetStringItem(i, 3, data.ip)
            if data.aps:
                self.SetStringItem(i, 4, ', '.join(data.aps))
        else:
            wx.ListCtrl.SetItem(self, data)
