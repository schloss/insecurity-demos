#!/usr/bin/env python

"""The main graphical user interface for Insecurity Demos"""

import wx
import wx.animate
from wx.lib.utils import AdjustRectToScreen
from panels import *
import wlan

class InsecurityDemosGUI(wx.App):
    """The main entry point for the Insecurity Demos application."""

    def __init__(self, demos):
        self.demos = demos # XXX : meh
        wx.App.__init__(self, redirect=False)

    def OnInit(self):
        """Called just before the application starts."""
        frame = MainFrame(self.demos) # XXX : meh
        self.SetTopWindow(frame)
        frame.Show()
        return True

class MainFrame(wx.Frame):
    """The top-level GUI element of the Plover application."""

    # Class constants.
    TITLE = "Insecurity Demos"
    BORDER = 5
    START_LABEL = "Start"
    STOP_LABEL = "Stop"
    REFRESH_LABEL = "Refresh"
    DEMO_LABEL = "Demo:"
    NETWORK_LABEL = "Network Interface:"

    def __init__(self, demos):
        wx.Frame.__init__(self, None, title=self.TITLE)
        self.Bind(wx.EVT_CLOSE, self._quit)

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
        self.status_button.Bind(wx.EVT_BUTTON, self._toggle_status)

        # Demo selection.
        demo_titles = [x.title for x in demos]
        self.demos = dict([(x.title, x) for x in demos])
        self.demo_choice = wx.Choice(self, -1, choices=demo_titles)
        self.demo_choice.Bind(wx.EVT_CHOICE, self._select_demo)

        # Network interface selection.
        self.network_choice = wx.Choice(self, -1,
                                        size=wx.Size(200, -1),
                                        choices=[])
        self.network_refresh = wx.Button(self, label=self.REFRESH_LABEL)
        self.network_refresh.Bind(wx.EVT_BUTTON, self._wireless_refresh)

        # Layout.
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        flags = wx.ALL | wx.ALIGN_CENTER_VERTICAL
        demo_box = wx.StaticBox(self, -1, self.DEMO_LABEL)
        demo_sizer = wx.StaticBoxSizer(demo_box, wx.HORIZONTAL)
        demo_sizer.Add(self.status_button, flag=flags, border=self.BORDER)
        #sizer.Add(demo_label, flag=flags, border=self.BORDER)
        demo_sizer.Add(self.demo_choice, flag=flags, border=self.BORDER)
        sizer.Add(demo_sizer, flag=flags, border=self.BORDER)

        network_box = wx.StaticBox(self, -1, self.NETWORK_LABEL)
        network_sizer = wx.StaticBoxSizer(network_box, wx.HORIZONTAL)
        #sizer.Add(network_label, flag=flags, border=self.BORDER)
        network_sizer.Add(self.network_choice, flag=flags, border=self.BORDER)
        network_sizer.Add(self.network_refresh, flag=flags, border=self.BORDER)
        sizer.Add(network_sizer, flag=flags, border=self.BORDER)

        global_sizer = wx.BoxSizer(wx.VERTICAL)
        global_sizer.Add(sizer)
        self.SetSizer(global_sizer)
        global_sizer.Fit(self)
        self.SetRect(AdjustRectToScreen(self.GetRect()))

        # Load data.
        self._wireless_refresh()

    def _get_network_interface(self):
        index = self.network_choice.GetSelection()
        if index < 0:
            return None
        return self.network_choice.GetItems()[index]

    def _wireless_refresh(self, event=None):
        self.Enable(False)
        current_interface = self._get_network_interface()
        interfaces = wlan.enumerate_interfaces()
        interface_names = [i.interface_name for i in interfaces]
        self.network_choice.SetItems(interface_names)
        if interface_names:
            if current_interface in interface_names:
                index = interface_names.index(current_interface)
            else:
                index = 0
            self.network_choice.SetSelection(index)
        self.Enable(True)

    def _toggle_status(self, event):
        label = self.status_button.GetLabel()
        if label == self.START_LABEL:
            label = self.STOP_LABEL
        else:
            label = self.START_LABEL
        self.status_button.SetLabel(label)
        for control in (self.demo_choice,
                        self.network_choice,
                        self.network_refresh):
            control.Enable(label == self.START_LABEL)

    def _select_demo(self, event):
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
    demos = [WLANProbesPanel, HTTPCapturePanel]
    app = InsecurityDemosGUI(demos=demos)
    app.MainLoop()
