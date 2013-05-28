#!/usr/bin/env python

import wx
from panels import *

class IntroPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)
		self.text_ctrl_1 = wx.TextCtrl(self, -1, "Welcome to information security demos!", style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_AUTO_URL|wx.TE_LINEWRAP|wx.TE_WORDWRAP)

		sizer = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(self.text_ctrl_1, wx.EXPAND, wx.EXPAND, 0)
		self.SetSizer(sizer)


firstdemo = "Intro"
demos = [
	('Intro', IntroPanel),
	('Key logging', KeyLoggerPanel),
	('Packet sniffing', PacketSnifferPanel),
	('Password cracking', PasswordCrackerPanel),
]


class InfoSecMainWindow(wx.Frame):
	def __init__(self, *args, **kwds):
		self.demos = {}

		kwds["style"] = wx.DEFAULT_FRAME_STYLE
		kwds["size"] = (550, 400)
		kwds["parent"] = None
		wx.Frame.__init__(self, *args, **kwds)
		self.SetTitle("Information Security Threat Demos")
		self.SetMinSize((500,350))

		self.demolist = wx.ListBox(self, -1, choices=[x[0] for x in demos])

		sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer_1.Add(self.demolist, 0, wx.EXPAND, 0)

		for i in dict(demos).keys():
			self.demos[i] = dict(demos)[i](self)
			sizer_1.Add(self.demos[i], 1, wx.EXPAND, 0)
			self.demos[i].Hide()

		self.curdemo = firstdemo
		self.demos[self.curdemo].Show()
		self.demolist.SetSelection(self.demolist.Items.index(self.curdemo))

		self.demolist.Bind(wx.EVT_LISTBOX, self.select_demo)

		self.SetSizer(sizer_1)
		sizer_1.Fit(self)
		self.Layout()

	def select_demo(self, event):
		self.demos[self.curdemo].Hide()
		self.curdemo = self.demolist.Items[event.Selection]
		self.demos[self.curdemo].Show()
		self.Layout()

if __name__ == "__main__":
	app = wx.App(redirect=False)
	top = InfoSecMainWindow()
	top.Show()
	app.MainLoop()
