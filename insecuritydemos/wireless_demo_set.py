import json
import wlan
import wx
import wx.lib.mixins.listctrl as listmixins
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
    DATA_COLUMN_LABELS = ['MAC Address',
                          'Nickname',
                          'Wifi Card',
                          'IP Address',
                          'Wifi Networks Previously Used']
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
        self.users = {}
        self.anonymity = True

    def initialize_data(self):
        self.wireless_refresh()

    def set_anonymity(self, anonymity):
        self.anonymity = anonymity
        for user in self.users.values():
            user.anonymous = anonymity
            self.data_grid.SetItem(user)

    def merge_users(self, new_users):
        for new_user in new_users:
            user = self.users.get(new_user.mac)
            if user:
                user.merge(new_user)
            else:
                user = new_user
                self.users[user.mac] = user
            self.data_grid.SetItem(user)

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
                old_user = self.users.get(new_user.mac)
                new_user.anonymity = self.anonymity
                if old_user:
                    old_user.anonymity = self.anonymity
                    old_user.merge(new_user)
                    self.data_grid.SetItem(old_user)
                else:
                    self.users[new_user.mac] = new_user
                    self.data_grid.SetItem(new_user)

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
        self.data_grid.Bind(wx.EVT_LIST_END_LABEL_EDIT, self._item_edited)

    def _get_grid_item(self, row):
        mac = self.data_grid.GetItem(row, 0).GetText()
        return self.users.get(mac, None)

    def _item_edited(self, event):
        row = event.m_itemIndex
        col = event.m_col
        text = event.m_item.GetText()
        user = self._get_grid_item(row)
        if user:
            self.data_grid.export_to_user(col, text, user)
        else:
            print "Oops, something unexpected happened when editing."

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


class WirelessDataList(wx.ListCtrl,
                       listmixins.ListCtrlAutoWidthMixin,
                       listmixins.TextEditMixin,
                       listmixins.ColumnSorterMixin):

    APS_SEPARATOR = ', '
    NICKNAME_COLUMN = 1
    NUMBER_OF_COLUMNS = 5
    MAC_TO_INT = {}

    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        self.itemDataMap = {}
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
        listmixins.ColumnSorterMixin.__init__(self, self.NUMBER_OF_COLUMNS)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self._edit_started)

    def _edit_started(self, event):
        # Only allow edits in the nickname column.
        if event.m_col != self.NICKNAME_COLUMN:
            event.Veto()

    def SetItem(self, data):
        if isinstance(data, wlan.User):
            item_key = self.__mac_to_int(data.mac)
            i = self.FindItem(-1, data.mac)
            if i < 0:
                i = self.InsertStringItem(0, data.mac)
                self.SetItemData(i, item_key)
            if i < 0:
                return
            column_data = (data.mac,
                           data.nickname,
                           data.hardware,
                           data.ip,
                           len(data.aps))
            assert(len(column_data) == self.NUMBER_OF_COLUMNS)
            self.itemDataMap[item_key] = column_data
            if data.nickname:
                self.SetStringItem(i, self.NICKNAME_COLUMN, data.nickname)
            if data.hardware:
                self.SetStringItem(i, 2, data.hardware)
            if data.ip:
                self.SetStringItem(i, 3, data.ip)
            if data.aps:
                if data.anonymous:
                    aps_list = [self.obscure_text(x) for x in data.aps]
                    aps = self.APS_SEPARATOR.join(aps_list)
                else:
                    aps = self.APS_SEPARATOR.join(data.aps)
                self.SetStringItem(i, 4, aps)
            # Re-sort list if it's already been sorted.
            col, ascending = self.GetSortState()
            if col >= 0:
                self.SortListItems(col, ascending)
        else:
            wx.ListCtrl.SetItem(self, data)

    def export_to_user(self, col, text, user):
        if col == self.NICKNAME_COLUMN:
            user.nickname = text
        else:
            print "Oops, can't edit user columns other than 'nickname'."
        self.SetItem(user)

    def obscure_text(self, text):
        x = len(text)
        if x > 7:
            return text[:3] + "*"*(x-6) + text[-3:]
        elif x > 2:
            return text[0] + "*"*(x-2) + text[-1]
        else:
            return "*"*x

    def __mac_to_int(self, mac):
        if mac in self.MAC_TO_INT:
            return self.MAC_TO_INT[mac]
        else:
            out = len(self.MAC_TO_INT)
            self.MAC_TO_INT[out] = mac
            return out

    # Required for the ColumnSorterMixin.
    def GetListCtrl(self):
        return self
