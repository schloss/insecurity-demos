#!/usr/bin/env python

import wx
import os
import subprocess
import fcntl
import sys
from threading import Thread
from Queue import Queue, Empty

def enqueue_output(out, queue):
	for line in iter(out.readline, b''):
		queue.put(line)
	out.close()


class WLANProbesPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)
		self.btn_capture_toggle = wx.Button(self, -1, "Start capture", style=wx.BU_LEFT|wx.BU_TOP)
		self.devices_list = wx.Choice(self, -1, choices=self.get_devices())
		self.capture_list = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.update, self.timer)
		self.tshark = None
		self.index = 0

		self.btn_capture_toggle.Bind(wx.EVT_BUTTON, self.toggle_capture)

		sizer = wx.FlexGridSizer(2, 1, 0, 1)
		sizer_toolbar = wx.BoxSizer(wx.HORIZONTAL)
		sizer_toolbar.Add(self.btn_capture_toggle, 0, 0, 0)
		sizer_toolbar.Add(wx.StaticText(self, -1, "Monitoring device:"), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer_toolbar.Add(self.devices_list, 0, 0, 0)
		sizer.Add(sizer_toolbar, 1, wx.EXPAND, 0)
		sizer.Add(self.capture_list, 1, wx.EXPAND, 1)
		self.SetSizer(sizer)
		sizer.AddGrowableCol(0)
		sizer.AddGrowableRow(1)

		self.capture_list.InsertColumn(0, 'Device')
		self.capture_list.InsertColumn(1, 'Polling')
		self.capture_list.SetColumnWidth(0, 80)
		self.capture_list.SetColumnWidth(1, 600)

		self.Layout()


	def update(self, event):
		if not self.tshark:	# should be redundant, but let's be sure.
			return

		while True:
			try:  line = self.queue.get_nowait()
			except Empty:
				break

			line = line.strip()
	
			fields = line.split(",")
			if fields[1] == "":
				continue


			ind = self.capture_list.FindItem(-1, fields[0], False)
			if ind != -1:
				old = self.capture_list.GetItem(ind, 1)
				new = [x.strip() for x in old.GetText().split(",")]
				new.append(fields[1])
				new = ", ".join(set(new))
				self.capture_list.SetStringItem(ind, 1, new)
			else:
				self.capture_list.InsertStringItem(self.index, fields[0])
				self.capture_list.SetStringItem(self.index, 1, fields[1])
				self.index += 1


	
	def toggle_capture(self, event):
		if self.tshark:
			print "Stopping capture..."
			self.stop_capture(event)
			self.btn_capture_toggle.SetLabel("Start capture")
		else:
			print "Starting capture..."
			self.start_capture(event)
			self.btn_capture_toggle.SetLabel("Stop capture")


	def start_capture(self, event=None):
		self.devname = self.devices_list.GetItems()[self.devices_list.GetCurrentSelection()]
		print "Starting airmon-ng..."
		#output = subprocess.Popen("airmon-ng start %s" % self.devname, shell=True, 
		#	stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
		#output.wait()
		print "Starting tshark..."

		self.tshark = subprocess.Popen("tshark -n -i %s -l -T fields -E separator=, -R 'wlan.fc.type_subtype eq 4' -e wlan.sa -e wlan_mgt.ssid subtype probereq" % self.devname, 
			shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
			stderr=subprocess.PIPE, close_fds=False, bufsize=10)


		self.queue = Queue()
		self.queuethread = Thread(target=enqueue_output, args=(self.tshark.stdout, self.queue))

		self.queuethread.daemon = True
		self.queuethread.start()

		self.timer.Start(1000)


	def stop_capture(self, event=None):
		self.timer.Stop()
		self.tshark.terminate()
		self.tshark.kill()
		self.tshark = None

		#output = subprocess.Popen("airmon-ng stop %s" % self.devname, shell=True, close_fds=True)
		#output.wait()


	def get_devices(self):
		# FIXME: Slow way of doing this.
		lines = subprocess.check_output("airmon-ng | awk '{ print $1 }' | tail --lines=+5 | head --lines=-1", shell=True)
		devs = lines.split()
		return devs
