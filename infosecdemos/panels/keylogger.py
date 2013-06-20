#!/usr/bin/env python

import wx

class KeyLoggerPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)
		self.text_ctrl_1 = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_AUTO_URL|wx.TE_LINEWRAP|wx.TE_WORDWRAP)
		self.btn_keylogger_start = wx.Button(self, -1, "Start Keylogger")
		self.btn_keylogger_stop = wx.Button(self, -1, "Stop Keylogger")

		sizer_2 = wx.BoxSizer(wx.VERTICAL)
		sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_2.Add(self.text_ctrl_1, wx.EXPAND, wx.EXPAND, 0)
		sizer_3.Add(self.btn_keylogger_start, 0, 2, 0)
		sizer_3.Add(self.btn_keylogger_stop, 0, 2, 0)
		sizer_2.Add(sizer_3, 1, 0, 1)
		self.SetSizer(sizer_2)


