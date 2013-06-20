#!/usr/bin/env python

import wx
import os

class PacketSnifferPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)
		self.btn_wireshark_start = wx.Button(self, -1, "Start Wireshark")
		self.btn_wireshark_start.Bind(wx.EVT_BUTTON, self.start_wireshark)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.btn_wireshark_start, 0, 0, 0)
		self.SetSizer(sizer)

	def start_wireshark(self, event):
		os.system("gksudo wireshark &")

