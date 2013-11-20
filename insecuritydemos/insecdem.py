#!/usr/bin/env python

"""The main graphical user interface for Insecurity Demos"""

import wx
from wx.lib.utils import AdjustRectToScreen
import wlan
from wireless_demo import WirelessDemo

class InsecurityDemosFrame(wx.Frame):
    """The top-level GUI element of the Plover application."""

    # Class constants.
    TITLE = "Insecurity Demos"
    BORDER = 5
    START_LABEL = "Start"
    STOP_LABEL = "Stop"
    DEMO_LABEL = "Demo"

    def __init__(self, parent, log):
        self.log = log # XXX : This should be used throughout
        wx.Frame.__init__(self, parent, title=self.TITLE)
        self.Bind(wx.EVT_CLOSE, self._quit)
        self.demos = WirelessDemo.DEMOS
        self.current_demo_set = WirelessDemo(self)

        # Menu bar.
        MENU_QUIT = 101
        MENU_ABOUT = 201
        menu_bar = wx.MenuBar()

        # File menu.
        file_menu = wx.Menu()
        file_menu.Append(MENU_QUIT, "Quit\tCtrl+Q")
        self.Bind(wx.EVT_MENU, self._quit, id=MENU_QUIT)
        menu_bar.Append(file_menu, "File")

        # Help menu.
        help_menu = wx.Menu()
        help_menu.Append(MENU_ABOUT, "&About %s..." % self.TITLE)
        self.Bind(wx.EVT_MENU, self._show_about_dialog, id=MENU_ABOUT)
        menu_bar.Append(help_menu, "Help")
        self.SetMenuBar(menu_bar)

        # Start and stop toggle.
        self.status_button = wx.Button(self, label=self.START_LABEL)
        self.status_button.Bind(wx.EVT_BUTTON, self._status_toggled)

        # Demo selection.
        self.demo_choice = wx.Choice(self, -1, choices=self.demos)
        self.demo_choice.Bind(wx.EVT_CHOICE, self._demo_selected)

        # Layout.
        flags = wx.ALL | wx.ALIGN_CENTER_VERTICAL
        demo_box = wx.StaticBox(self, -1, self.DEMO_LABEL)
        demo_sizer = wx.StaticBoxSizer(demo_box, wx.HORIZONTAL)
        demo_sizer.Add(self.status_button, flag=flags, border=self.BORDER)
        demo_sizer.Add(self.demo_choice, flag=flags, border=self.BORDER)

        control_sizer = wx.BoxSizer(wx.HORIZONTAL)
        control_sizer.Add(demo_sizer, flag=flags, border=self.BORDER)
        control_sizer.Add(self.current_demo_set.control_panel)

        global_sizer = wx.BoxSizer(wx.VERTICAL)
        global_sizer.Add(control_sizer)
        global_sizer.Add(self.current_demo_set.data_panel, flag=wx.EXPAND)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)
        self.SetRect(AdjustRectToScreen(self.GetRect()))

        # Load data.
        self.current_demo_set.initialize_data()

    def _status_toggled(self, event):
        label = self.status_button.GetLabel()
        if label == self.START_LABEL:
            label = self.STOP_LABEL
        else:
            label = self.START_LABEL
        self.status_button.SetLabel(label)
        is_enabled = label == self.STOP_LABEL
        self.demo_choice.Enable(not is_enabled)
        self.current_demo_set.enable_control_panel(not is_enabled)
        self.current_demo_set.enable_demo('foo', is_enabled)

    def _demo_selected(self, event):
        print "Selected the \"%s\" demo." % self.demo_choice.GetSelection()

    def _quit(self, event):
        self.Destroy()

    def _show_about_dialog(self, event=None):
        """Called when the About... button is clicked."""
        info = wx.AboutDialogInfo()
        info.Name = self.TITLE
        info.Version = '0.0.1'
        info.Copyright = '(C) Schloss 2013'
        info.Description = ('A packaged, graphical user interface for '
                            'demonstrating various digital security threats '
                            'and mitigations. It is intended for standalone '
                            'functionality in a training room context.')
        info.WebSite = 'https://github.com/schloss/insecurity-demos'
        info.Developers = ['D.G. Vole',
                           'Smari McCarthy',
                           'Poser',
                           'Samir Nassar']
        info.License = 'GNU General Public License, version 3'
        wx.AboutBox(info)

if __name__ == "__main__":
    import sys
    app = wx.App()
    frame = InsecurityDemosFrame(None, sys.stdout)
    frame.Show(True)
    app.MainLoop()
