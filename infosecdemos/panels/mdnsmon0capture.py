#!/usr/bin/env python

### 
# <description>
### 

import wx
import os
import subprocess
import fcntl

class MDNSMon0CapturePanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent)
		self.btn_monitor_toggle = wx.Button(self, -1, "Start monitor mode", style=wx.BU_LEFT|wx.BU_TOP)

		self.btn_capture_toggle = wx.Button(self, -1, "Start capture")

		self.devices_list = wx.Choice(self, -1, choices=self.get_devices())
		self.capture_list = wx.ListCtrl(self, -1, style=wx.LC_REPORT|wx.SUNKEN_BORDER)

		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.update, self.timer)

		self.tshark = None

		self.btn_capture_toggle.Bind(wx.EVT_BUTTON, self.toggle_capture)
		self.btn_monitor_toggle.Bind(wx.EVT_BUTTON, self.toggle_monitor)
                # TODO: bind capture_list change event to set btn_monitor_toggle text appropriately
                self.devices_list.Bind(wx.EVT_CHOICE, self.interface_selected)

		sizer = wx.FlexGridSizer(2, 1, 0, 1)
		sizer_toolbar = wx.BoxSizer(wx.HORIZONTAL)
		sizer_toolbar.Add(self.btn_monitor_toggle, 0, 0, 0)
		sizer_toolbar.Add(self.btn_capture_toggle, 0, 0, 0)
		sizer_toolbar.Add(wx.StaticText(self, -1, "Monitoring device:"), 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0)
		sizer_toolbar.Add(self.devices_list, 0, 0, 0)
		sizer.Add(sizer_toolbar, 1, wx.EXPAND, 0)
		sizer.Add(self.capture_list, 1, wx.EXPAND, 1)
		self.SetSizer(sizer)
		sizer.AddGrowableCol(0)
		sizer.AddGrowableRow(1)
		self.Layout()

                # Set monitor mode toggle button appropriately based on selected interface
                try:
	                self.devname = self.devices_list.GetItems()[self.devices_list.GetCurrentSelection()]
	                if self.devname[0:3] == "mon":
                                self.btn_monitor_toggle.SetLabel("Stop monitor mode")
                except:
                        pass

	def update(self, event):
		if not self.tshark:	# should be redundant, but let's be sure.
			return

		print "Getting lines..."
		while True: #self.tshark.poll() is not None:
			try:
				line = self.tshark.stdout.readline()
				print "Got lines: '%s'" % line
			except IOError, e:
				break

        def interface_selected(self, event):
                self.devname = self.devices_list.GetItems()[self.devices_list.GetCurrentSelection()]
                if self.devname[0:3] == "mon":
                        self.btn_monitor_toggle.SetLabel("Stop monitor mode")
                else:
                        self.btn_monitor_toggle.SetLabel("Start monitor mode")
                

        def toggle_monitor(self, event):
                self.devname = self.devices_list.GetItems()[self.devices_list.GetCurrentSelection()]
                if self.devname[0:3] == "mon":
                        print "Stopping monitor mode on %s" % self.devname
                        self.stop_monitor_mode(event)
                        self.btn_monitor_toggle.SetLabel("Select interface")
                else:
                        if self.devname[0:3]:
                                print "Starting monitor mode on %s" % self.devname
                                self.start_monitor_mode(event)
                                self.btn_monitor_toggle.SetLabel("Select interface")
                # If no interface is selected, do nothing
                # TODO: handle other possible interface names (ethX, wifiX, etc.)

        def start_monitor_mode(self, event=None):
		self.devname = self.devices_list.GetItems()[self.devices_list.GetCurrentSelection()]
		lines = subprocess.check_output("gksudo airmon-ng start %s" % self.devname, shell=True)
                # print lines   # DEBUG
		self.devices_list.SetItems(self.get_devices())
                ### TODO: refresh devices_list (or select "most recent" device?)
        

        def stop_monitor_mode(self, event=None):
		self.devname = self.devices_list.GetItems()[self.devices_list.GetCurrentSelection()]
 		lines = subprocess.check_output("gksudo airmon-ng stop %s" % self.devname, shell=True)
                # print lines   # DEBUG
		self.devices_list.SetItems(self.get_devices())
                ### TODO: refresh devices_list (or select "least recent" device?)
                self.btn_monitor_toggle.SetLabel("Select interface")

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
		output = subprocess.Popen("gksudo airmon-ng start %s" % self.devname, shell=True, 
			stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
		output.wait()
		print "Starting tshark..."
		#self.tshark = subprocess.Popen("gksudo tshark -n -T fields -e dns.qry.name -i %s -R 'udp.srcport == 5353'" % self.devname, 
		#	shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
		#	stderr=subprocess.PIPE, close_fds=True)

		self.tshark = subprocess.Popen("gksudo tshark -n -T fields -e http.host -i %s -R 'http'" % self.devname, 
			shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE, close_fds=True)

		fl = fcntl.fcntl(self.tshark.stdout, fcntl.F_GETFL)
		fcntl.fcntl(self.tshark.stdout, fcntl.F_SETFL, fl | os.O_NONBLOCK)

		self.timer.Start(1000)

	def stop_capture(self, event=None):
		self.timer.Stop()
		self.tshark.terminate()
		self.tshark = None

		output = subprocess.Popen("gksudo airmon-ng stop %s" % self.devname, shell=True, close_fds=True)
		output.wait()

	def get_devices(self):
		# FIXME: Slow way of doing this.
		lines = subprocess.check_output("fakeroot airmon-ng | awk '{ print $1 }' | tail --lines=+5 | head --lines=-1", shell=True)
		devs = lines.split()
		return devs
