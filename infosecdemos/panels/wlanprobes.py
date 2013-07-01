#!/usr/bin/env python
from tsharkpanel import GenericTSharkPanel

class WLANProbesPanel(GenericTSharkPanel):
	def __init__(self, parent):
		GenericTSharkPanel.__init__(self, parent, "-R 'wlan.fc.type_subtype eq 4' -e wlan.sa -e wlan_mgt.ssid subtype probereq")
		self.addfield("Device", 80)
		self.addfield("Polling", 600)
		self.capture_list.Bind(wx.wxEVT_LEFT_DCLICK, self.showdetails)

	def showdetails(self, event):
		selected = self.capture_list.GetFirstSelected()
		if selected < 0:
			return
		
		item = self.capture_list.GetItem(selected)
		print item
