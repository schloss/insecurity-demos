#!/usr/bin/env python

"""The main graphical user interface for Insecurity Demos"""

import os.path
import wx
import wx.html
from wx.lib.utils import AdjustRectToScreen
import wlan
from wireless_demo_set import WirelessDemoSet

class InsecurityDemosFrame(wx.Frame):
    """The top-level GUI element of the Plover application."""

    # Class constants.
    TITLE = "Insecurity Demos"
    BORDER = 5
    START_LABEL = "Start"
    STOP_LABEL = "Stop"
    DEMO_LABEL = "Demo"
    NOTES_LABEL = "Notes"

    def __init__(self, parent, log):
        self.log = log # XXX : This should be used throughout
        wx.Frame.__init__(self, parent, title=self.TITLE)
        self.Bind(wx.EVT_CLOSE, self._quit)
        self.current_demo_set = WirelessDemoSet(self)
        self.demos = self.current_demo_set.demo_names()

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

        # Training notes.
        self.notes_button = wx.Button(self, label=self.NOTES_LABEL)
        self.notes_button.Bind(wx.EVT_BUTTON, self._notes_pressed)
        self.notes_window = None

        # Layout.
        flags = wx.ALL | wx.ALIGN_CENTER_VERTICAL
        demo_box = wx.StaticBox(self, -1, self.DEMO_LABEL)
        demo_sizer = wx.StaticBoxSizer(demo_box, wx.HORIZONTAL)
        demo_sizer.Add(self.status_button, flag=flags, border=self.BORDER)
        demo_sizer.Add(self.demo_choice, flag=flags, border=self.BORDER)
        demo_sizer.Add(self.notes_button, flag=flags, border=self.BORDER)

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
        self._demo_selected()

    def _status_toggled(self, event):
        label = self.status_button.GetLabel()
        if label == self.START_LABEL:
            label = self.STOP_LABEL
        else:
            label = self.START_LABEL
        self.status_button.SetLabel(label)
        is_enabled = label == self.STOP_LABEL
        self.demo_choice.Enable(not is_enabled)
        demo_name = self.demo_choice.GetStringSelection()
        self.current_demo_set.enable_demo( demo_name, is_enabled)

    def _demo_selected(self, event=None):
        demo = self.demo_choice.GetStringSelection()
        self._update_notes(demo)
        self.current_demo_set.select_demo(demo)

    def _notes_pressed(self, event):
        if not self.notes_window:
            self.notes_window = wx.Frame(None, size=wx.Size(700,700))
            self.html = wx.html.HtmlWindow(self.notes_window)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.html, 1, wx.GROW)
            self.notes_window.SetSizer(sizer)
            self.notes_window.Show()
            demo = self.demo_choice.GetStringSelection()
            self._update_notes(demo)
        else:
            self.notes_window.Raise()

    def _update_notes(self, demo):
        if self.notes_window:
            file_name = demo.replace(' ', '_')
            file_name = file_name.replace("'",'')
            file_name = file_name.replace('-','_')
            file_name = file_name.lower()
            file_name += ".html"
            file_name = os.path.join(os.path.dirname(__file__),
                                     'demos',
                                     file_name)
            if os.path.isfile(file_name):
                self.html.LoadPage(file_name)
            else:
                self.html.SetPage("<html><body>There are no notes for the "
                                  "\"%s\" demo.</body></html>" % demo)

    def _quit(self, event):
        self.current_demo_set.destroy()
        if self.notes_window:
            self.notes_window.Destroy()
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
