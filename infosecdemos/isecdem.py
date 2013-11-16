#!/usr/bin/env python

import wx
from panels import *

class IntroPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.text_ctrl_1 = wx.TextCtrl(self,
                                       -1,
                                       "Welcome to information security demos!",
                                       style=(wx.TE_MULTILINE |
                                              wx.TE_READONLY |
                                              wx.TE_AUTO_URL |
                                              wx.TE_LINEWRAP |
                                              wx.TE_WORDWRAP))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text_ctrl_1, wx.EXPAND, wx.EXPAND, 0)
        self.SetSizer(sizer)

class InfoSecMainWindow(wx.Frame):
    def __init__(self, demos, default_demo):
        # Set basic parameters and call super.
        wx.Frame.__init__(self,
                          style = wx.DEFAULT_FRAME_STYLE,
                          size = (550, 400),
                          parent = None)
        self.SetTitle("Information Security Threat Demos")
        self.SetMinSize((500,350))
        self.Bind(wx.EVT_WINDOW_DESTROY, self.__quit)

        # Instantiate the demo list.
        ordered_demos = zip(*demos)[0]
        self.demolist = wx.ListBox(self, -1, choices=ordered_demos)
        self.demolist.Bind(wx.EVT_LISTBOX, self.__select_demo)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(self.demolist, 0, wx.EXPAND, 0)

        # Instantiate all demo panels.
        self.demos = {}
        for demo_name, demo_class in demos:
            demo = demo_class(self)
            self.demos[demo_name] = demo
            sizer_1.Add(demo, 1, wx.EXPAND, 0)
            demo.Hide()

        # Set the default demo.
        self.current_demo = default_demo
        self.demos[self.current_demo].Show()
        self.demolist.SetSelection(self.demolist.Items.index(self.current_demo))

        # Final layout.
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

    def __select_demo(self, event):
        self.demos[self.current_demo].Hide()
        self.current_demo = self.demolist.Items[event.Selection]
        self.demos[self.current_demo].Show()
        self.Layout()

    def __quit(self, event):
        self.demolist.Unbind(wx.EVT_LISTBOX, handler=self.__select_demo)

if __name__ == "__main__":

    # Configuration parameters.
    default_demo = "Intro"
    demos = [
        ('Intro', IntroPanel),
        ('Key logging', KeyLoggerPanel),
        ('Packet sniffing', PacketSnifferPanel),
        ('MDNS Capture 1', MDNSCapturePanel),
        ('MDNS Capture 2', MDNSMon0CapturePanel),
        ('HTTP Capture', HTTPCapturePanel),
        ('WLAN Probes', WLANProbesPanel),
        ('Password cracking', PasswordCrackerPanel),
    ]

    # Initialization.
    app = wx.App(redirect=False)
    top = InfoSecMainWindow(demos, default_demo)
    top.Show()
    app.MainLoop()
