import json
import os
import wlan
import wx
import wx.lib.newevent
import ObjectListView as olv
from demos import wireless_demos
from tools import TShark
from Queue import Empty

IMAGE_LOCKED = os.path.join(os.path.dirname(__file__),
                            'locked_small.png')
IMAGE_UNLOCKED = os.path.join(os.path.dirname(__file__),
                              'unlocked_small.png')

UserModifiedEvent, EVT_USER_MODIFIED = wx.lib.newevent.NewEvent()

class WirelessDemoSet():
    """A collection of wireless insecurity demos."""

    # Class constants.
    DEMOS = (wireless_demos.AccessPointDemo(),
             wireless_demos.HttpBasicAuthSniffDemo(),)
    BORDER = 5
    REFRESH_LABEL = "Refresh"
    NETWORK_INTERFACE_LABEL = "Network Interface"
    WIRELESS_NETWORK_LABEL = "Wireless Network"
    MONITOR_MODE_LABEL_OFF = "Monitor mode is OFF."
    SELECT_NETWORK_LABEL = "Select a network..."
    TSHARK_SEPARATOR = ','
    TSHARK_POLL_INTERVAL = 500

    def __init__(self, parent):
        self._polling_demo = None
        self.timer = wx.Timer()
        self.timer.Bind(wx.EVT_TIMER, self._poll_tools)
        self.tshark = None
        self.interfaces = []
        self.networks = []
        self._init_control_panel(parent)
        self._init_data_panel(parent)

    def get_users(self):
        return self.data_grid.GetObjects()

    def initialize_data(self):
        self._interface_refresh()

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
                users_dict[new_user.mac] = new_user
        self.data_grid.SetObjects(users_dict.values())

    def destroy(self):
        for i in self.interfaces:
            if i.monitor_mode:
                i.disable_monitor_mode()

    def _poll_tools(self, event):
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
                # Access points aren't users.
                for network in self.networks:
                    if new_user.mac == network.bssid:
                        new_user = None
                        break
                if not new_user:
                    continue
                # Match the user's network's BSSID to a known ESSID.
                if (new_user.current_network and
                    new_user.current_network.bssid and
                    not new_user.current_network.essid):
                    bssid = new_user.current_network.bssid
                    for network in self.networks:
                        if network.bssid == bssid:
                            new_user.current_network.essid = network.essid
                            break
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
            self._enable_interface_panel(True)
            self._enable_network_panel(demo.WIRELESS_NETWORKS_CONTROL)
            if not demo.WIRELESS_NETWORKS_CONTROL:
                self.network_choice.SetSelection(0)
                self._network_selected()
        else:
            self._enable_interface_panel(False)
            self._enable_network_panel(False)

    def enable_demo(self, demo_title, is_enabled):
        demo = self._get_demo(demo_title)
        if not demo:
            return False

        # Check that the demo has everything it needs to start.
        network = self._get_network()
        if (is_enabled and
            demo.REQUIRES_NETWORK and
            not network):
            dialog = wx.MessageDialog(self.control_panel,
                                      "Please select a wireless network "
                                      "and try again.",
                                      "Network Required",
                                      wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()
            return False
        if (is_enabled and
            demo.REQUIRES_NETWORK_PASSWORD and
            not network.password):
            dialog = wx.MessageDialog(self.control_panel,
                                      "Please enter a password for the "
                                      "wireless network and try again.",
                                      "Password Required",
                                      wx.OK | wx.ICON_INFORMATION)
            dialog.ShowModal()
            dialog.Destroy()
            return False

        # Enable UI elements as appropriate.
        self._enable_network_panel(not is_enabled and
                                   demo.WIRELESS_NETWORKS_CONTROL)
        self._enable_interface_panel(not is_enabled)
        wx.CallAfter(self._enable_demo, demo, is_enabled)
        return is_enabled

    def _enable_demo(self, demo, is_enabled):
        if not is_enabled:
            self.timer.Stop()
            self.tshark.stop_capture()
            self.tshark = None
            self._polling_demo = None
            return
        # Update the list of available networks before every demo.
        self._network_refresh()
        # Determine the channel of the network to monitor, if any.
        network = self._get_network()
        if network:
            channel = network.channel
        else:
            channel = None
        # Put the interface into the correct mode.
        interface = self._get_interface()
        if (interface.monitor_mode and
            interface.monitor_mode_channel != channel):
            interface.disable_monitor_mode()
            self._interface_refresh()
            interface = self._get_interface()
        if demo.MONITOR_MODE and not interface.monitor_mode:
            interface.enable_monitor_mode(channel)
            self._interface_refresh()
        elif not demo.MONITOR_MODE and interface.monitor_mode:
            interface.disable_monitor_mode()
            self._interface_refresh()
        # Start TShark with the demo parameters.
        self._polling_demo = demo
        interface = self._get_interface()
        interface_name = interface.monitor_mode or interface.interface_name
        if demo.TSHARK_SUPPLY_PASSWORD:
            prefs = (demo.TSHARK_PREFERENCES +
                     ['uat:80211_keys:\\"wpa-pwd\\",\\"%s:%s\\"' %
                      (network.password, network.essid)])
        else:
            prefs = demo.TSHARK_PREFERENCES
        self.tshark = TShark(interface=interface_name,
                             fields=demo.TSHARK_FIELDS,
                             separator=self.TSHARK_SEPARATOR,
                             capture_filter=demo.TSHARK_CAPTURE_FILTER,
                             read_filter=demo.TSHARK_READ_FILTER,
                             preferences=prefs)

        self.tshark.start_capture()
        self.timer.Start(self.TSHARK_POLL_INTERVAL)

    def _enable_network_panel(self, is_enabled):
        for control in (self.network_choice,
                        self.network_refresh_button):
            control.Enable(is_enabled)
        if is_enabled:
            self._network_selected()

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

    def _get_network(self):
        if self.network_choice.GetSelection() > 0:
            name = self.network_choice.GetStringSelection()
            for n in self.networks:
                if str(n) == name:
                    return n
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
                                           self._interface_refresh)
        self.monitor_mode_label = wx.StaticText(self.control_panel, -1,
                                                self.MONITOR_MODE_LABEL_OFF)

        # Wireless network selection.
        self.network_choice = wx.Choice(self.control_panel, -1,
                                        size=wx.Size(300, -1),
                                        choices=[])
        self.network_choice.Bind(wx.EVT_CHOICE,
                                 self._network_selected)
        self.network_refresh_button = wx.Button(self.control_panel,
                                                label=self.REFRESH_LABEL)
        self.network_refresh_button.Bind(wx.EVT_BUTTON, self._network_refresh)

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
        self.data_grid = olv.ObjectListView(self.data_panel,
                                            wx.ID_ANY,
                                            size=(-1,600),
                                            style=(wx.LC_REPORT |
                                                   wx.LC_VRULES |
                                                   wx.SUNKEN_BORDER))
        self.data_grid.AddNamedImages("locked",
                                      wx.Bitmap(IMAGE_LOCKED))
        self.data_grid.AddNamedImages("unlocked",
                                      wx.Bitmap(IMAGE_UNLOCKED))
        sniffable_column = olv.ColumnDefn(title="?",
                                          fixedWidth=40,
                                          align="left",
                                          isEditable=False,
                                          imageGetter=locked_getter)
        creds_column = olv.ColumnDefn("Credentials",
                                      "left",
                                      175,
                                      valueGetter="credentials_to_string",
                                      isEditable=False,
                                      minimumWidth=175,
                                      isSpaceFilling=True,
                                      checkStateGetter="anonymous_creds")
        networks_column = olv.ColumnDefn("Previous Wifi Networks",
                                         "left",
                                         175,
                                         valueGetter="aps_to_string",
                                         isEditable=False,
                                         minimumWidth=175,
                                         isSpaceFilling=True,
                                         checkStateGetter="anonymous_aps")
        value_getter = "current_network_to_string"
        self.current_network_column = olv.ColumnDefn(title="Last Wifi Network",
                                                     align="left",
                                                     width=175,
                                                     valueGetter=value_getter,
                                                     isEditable=False)
        cols = [sniffable_column,
                olv.ColumnDefn("MAC Address", "left", 175, "mac",
                               isEditable=False),
                olv.ColumnDefn("Nickname", "left", 175,
                               valueGetter="nickname_to_string",
                               valueSetter="nickname_from_string"),
                olv.ColumnDefn("Wifi Chipset", "left", 175, "hardware",
                               isEditable=False),
                olv.ColumnDefn("IP Address", "left", 175, "ip", isEditable=False),
                #olv.ColumnDefn("Hostname", "left", 175, "hostname", isEditable=False),
                self.current_network_column,
                creds_column,
                networks_column]
        self.sniffable_column_index = cols.index(sniffable_column)
        self.credentials_column_index = cols.index(creds_column)
        self.networks_column_index = cols.index(networks_column)
        self.data_grid.SetColumns(cols)
        self.data_grid.SetEmptyListMsg("Start a demo or use \"File > Import\""
                                       " to populate this list.")
        self.data_grid.cellEditMode = olv.ObjectListView.CELLEDIT_DOUBLECLICK
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
        self.data_grid.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._item_activated)
        self.data_grid.Bind(olv.EVT_SORT, self._column_sort)

    # Sort by number of elements, not string representation of list.
    def _column_sort(self, event):
        if event.sortColumnIndex in (self.credentials_column_index,
                                     self.networks_column_index,):
            self.data_grid.SortListItemsBy(length_sorter,
                                           event.sortAscending)
            event.wasHandled = True
        elif event.sortColumnIndex == self.sniffable_column_index:
            self.data_grid.SortListItemsBy(sniffable_sorter,
                                           event.sortAscending)

    def _item_activated(self, event):
        user = self.data_grid.GetSelectedObject()
        if user:
            user_frame = UserFrame(self.data_panel, -1, user=user)
            user_frame.Bind(EVT_USER_MODIFIED, self._user_modified)
            user_frame.Show()

    def _user_modified(self, event):
        self.data_grid.RefreshObject(event.user)

    def _interface_refresh(self, event=None):
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

        # Also, don't list anything that even looks like a monitoring
        # interface. Whether an interface is actually in monitor mode
        # could be better verified using something like iwconfig.
        for i in new_interfaces:
            if i.interface_name.startswith('mon'):
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

    def _network_selected(self, event=None):
        network = self._get_network()
        if network == None:
            f = None
        else:
            f = olv.Filter.TextSearch(self.data_grid,
                                      columns=(self.current_network_column,),
                                      text=network.essid)
            while not network.password:
                self._network_password_input()
        self.data_grid.SetFilter(f)
        self.data_grid.RepopulateList()

    def _network_refresh(self, event=None):
        interface = self.interface_choice.GetStringSelection()
        if not interface:
            self.network_choice.SetItems([])
        else:
            current_network = self.network_choice.GetStringSelection()
            old_networks = self.networks
            self.networks = wlan.enumerate_networks(interface)
            for n in self.networks:
                # Show only WPA and open networks.
                if not all(['WPA' in s for s in n.security]):
                    self.networks.remove(n)
                    continue
                # Retain previous information, like password.
                for old in old_networks:
                    if old == n:
                        n.merge(old)
            network_names = map(str, self.networks)
            if network_names:
                network_names.insert(0, self.SELECT_NETWORK_LABEL)
            self.network_choice.SetItems(network_names)
            if network_names:
                if current_network in network_names:
                    self.network_choice.SetStringSelection(current_network)
                else:
                    self.network_choice.SetSelection(0)
        self._network_selected()

    def _network_password_input(self):
        network = self._get_network()
        if not network:
            return
        dialog = wx.PasswordEntryDialog(self.control_panel,
                                        "Enter a password for the \"%s\""
                                        " network." % network.essid,
                                        "Network Password",
                                        network.password or '')
        status = dialog.ShowModal()
        if status == wx.ID_OK:
            password = dialog.GetValue()
            network.password = password
        dialog.Destroy()

def length_sorter(x, y):
    """Sort first by length and then by string representation."""
    x_len = len(x.aps)
    y_len = len(y.aps)
    if x_len < y_len:
        return -1
    elif x_len > y_len:
        return 1
    else:
        x_str = x.aps_to_string()
        y_str = y.aps_to_string()
        if x_str < y_str:
            return -1
        elif x_str > y_str:
            return 1
        else:
            return 0

def sniffable_sorter(x, y):
    if x.sniffable and not y.sniffable:
        return 1
    elif not x.sniffable and y.sniffable:
        return -1
    else:
        return 0

def locked_getter(user):
    if user.sniffable:
        return "unlocked"
    else:
        return "locked"

class UserFrame(wx.Frame):

    MENU_CLOSE = 101
    PARAM_BORDER = 4

    def __init__(self, parent, ID, user):
        self.user = user

        # Main window.
        title = "User %s" % user.mac
        if user.nickname:
            title += " (%s)" % user.nickname
        wx.Frame.__init__(self, parent, -1, title, size=(1000,400))

        # Menu bar.
        menu_bar = wx.MenuBar()
        file_menu = wx.Menu()
        file_menu.Append(self.MENU_CLOSE, "Close\tCtrl+W")
        self.Bind(wx.EVT_MENU, self._close, id=self.MENU_CLOSE)
        menu_bar.Append(file_menu, "File")
        self.SetMenuBar(menu_bar)

        # Basic parameters.
        panel = wx.Panel(self, -1)
        self.nickname = wx.TextCtrl(panel, -1)
        self.anonymous_aps = wx.CheckBox(panel, -1, "Previous Networks")
        self.anonymous_creds = wx.CheckBox(panel, -1, "Credentials")
        self.sniffable = wx.StaticBitmap(panel, -1)
        self.mac = wx.StaticText(panel, -1)
        self.hardware = wx.StaticText(panel, -1)
        self.ip = wx.StaticText(panel, -1)
        self.hostname = wx.StaticText(panel, -1)
        self.current_network = wx.StaticText(panel, -1)
        self.save = wx.Button(panel, -1, "Save")
        self.clear = wx.Button(panel, -1, "Clear Sensitive Data")

        self.nickname.Bind(wx.EVT_TEXT, self._user_modified)
        self.anonymous_aps.Bind(wx.EVT_CHECKBOX, self._user_modified)
        self.anonymous_creds.Bind(wx.EVT_CHECKBOX, self._user_modified)
        self.save.Bind(wx.EVT_BUTTON, self._save)
        self.clear.Bind(wx.EVT_BUTTON, self._clear)

        params = (('Nickname:', self.nickname),
                  ('Anonymous:', self.anonymous_creds),
                  ('', self.anonymous_aps),
                  ('Sniffable:', self.sniffable),
                  ('MAC:', self.mac),
                  ('Wifi Chipset:', self.hardware),
                  ('IP Address:', self.ip),
                  ('Hostname:', self.hostname),
                  ('Last Wifi Network:', self.current_network),
                  ('', self.save),
                  ('', self.clear))
        sizer = wx.FlexGridSizer(len(params), 2,
                                 self.PARAM_BORDER, self.PARAM_BORDER)
        for name, value_ui in params:
            name_label = wx.StaticText(panel, -1, name)
            sizer.Add(name_label,
                      flag=(wx.ALL | wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT),
                      border=self.PARAM_BORDER)
            sizer.Add(value_ui,
                      flag=(wx.ALL | wx.ALIGN_CENTER_VERTICAL |
                            wx.ALIGN_LEFT | wx.EXPAND),
                      border=self.PARAM_BORDER)
        panel.SetSizer(sizer)

        def anon_ap_string(text):
            if self.user.anonymous_aps:
                return wlan.obscure_text(text)
            else:
                return text

        def anon_cred_string(text):
            if self.user.anonymous_creds:
                return wlan.obscure_text(text)
            else:
                return text

        self.credentials = olv.ObjectListView(self, -1,
                                              size=(400,-1),
                                              style=(wx.LC_REPORT |
                                                     wx.LC_VRULES |
                                                     wx.SUNKEN_BORDER))
        username_column = olv.ColumnDefn("Username",
                                         "left",
                                         200,
                                         valueGetter="username",
                                         stringConverter=anon_cred_string)
        password_column = olv.ColumnDefn("Password",
                                         "left",
                                         200,
                                         valueGetter="password",
                                         stringConverter=anon_cred_string)
        self.credentials.SetColumns([username_column, password_column])
        self.credentials.SetEmptyListMsg("None.")
        self.credentials.SetObjects(user.credentials)

        self.networks = olv.ObjectListView(self, -1,
                                           size=(300,-1),
                                           style=(wx.LC_REPORT |
                                                  wx.LC_VRULES |
                                                  wx.SUNKEN_BORDER))
        network_column = olv.ColumnDefn("Previous Wifi Networks",
                                         "left",
                                         300,
                                         valueGetter="essid",
                                         stringConverter=anon_ap_string)
        self.networks.SetColumns([network_column])
        self.networks.SetEmptyListMsg("None.")
        self.networks.SetObjects(user.aps)

        self.update()

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(panel,
                  flag=(wx.ALL | wx.ALIGN_TOP | wx.EXPAND),
                  border=self.PARAM_BORDER)
        sizer.Add(self.credentials,
                  flag=(wx.ALL | wx.ALIGN_TOP | wx.EXPAND),
                  border=self.PARAM_BORDER)
        sizer.Add(self.networks,
                  flag=(wx.ALL | wx.ALIGN_TOP | wx.EXPAND),
                  border=self.PARAM_BORDER)

        self.SetSizer(sizer)

    def update(self):
        self.nickname.SetValue(self.user.nickname or '')
        self.anonymous_aps.SetValue(self.user.anonymous_aps)
        self.anonymous_creds.SetValue(self.user.anonymous_creds)
        if self.user.sniffable:
            self.sniffable.SetBitmap(wx.Bitmap(IMAGE_UNLOCKED))
        else:
            self.sniffable.SetBitmap(wx.Bitmap(IMAGE_LOCKED))
        self.mac.SetLabel(self.user.mac or '')
        self.hardware.SetLabel(self.user.hardware or '')
        self.ip.SetLabel(self.user.ip or '')
        self.hostname.SetLabel(self.user.hostname or '')
        self.current_network.SetLabel(self.user.current_network_to_string())
        self.credentials.SetObjects(self.user.credentials)
        self.networks.SetObjects(self.user.aps)
        self.save.Enable(False)

    def _close(self, event):
        self.Destroy()

    def _save(self, event):
        self.user.nickname = self.nickname.GetValue() or None
        self.user.anonymous_aps = self.anonymous_aps.GetValue()
        self.user.anonymous_creds = self.anonymous_creds.GetValue()
        self.save.Enable(False)
        self.update()
        event = UserModifiedEvent(user=self.user)
        wx.PostEvent(self, event)

    def _clear(self, event):
        self.user.aps = []
        self.user.credentials = []
        self.user.hostname = None
        self.user.ip = None
        self.update()
        event = UserModifiedEvent(user=self.user)
        wx.PostEvent(self, event)

    def _user_modified(self, event):
        self.save.Enable(True)
