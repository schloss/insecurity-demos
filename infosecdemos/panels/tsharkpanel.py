import wx
import Queue
from util import get_wireless_devices
import tshark

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class GenericTSharkPanel(wx.Panel):
    def __init__(self, parent, is_in_monitor_mode=False):
        self.is_in_monitor_mode = is_in_monitor_mode
        wx.Panel.__init__(self, parent=parent)
        self.btn_capture_toggle = wx.Button(self,
                                            -1,
                                            "Start capture",
                                            style=wx.BU_LEFT | wx.BU_TOP)
        self.devices_list = wx.Choice(self, -1, choices=get_wireless_devices())
        self.capture_list = wx.ListCtrl(self,
                                        -1,
                                        style=wx.LC_REPORT | wx.SUNKEN_BORDER)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.update, self.timer)
        self.tshark = None
        self.index = 0
        self.fields = []

        self.btn_capture_toggle.Bind(wx.EVT_BUTTON, self.toggle_capture)

        sizer = wx.FlexGridSizer(2, 1, 0, 1)
        sizer_toolbar = wx.BoxSizer(wx.HORIZONTAL)
        sizer_toolbar.Add(self.btn_capture_toggle, 0, 0, 0)
        sizer_toolbar.Add(wx.StaticText(self, -1, "Monitoring device:"),
                          0,
                          wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL,
                          0)
        sizer_toolbar.Add(self.devices_list, 0, 0, 0)
        sizer.Add(sizer_toolbar, 1, wx.EXPAND, 0)
        sizer.Add(self.capture_list, 1, wx.EXPAND, 1)
        self.SetSizer(sizer)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(1)

        self.Layout()

    def addfield(self, fieldname, length=None):
        self.fields.append(fieldname)
        self.capture_list.InsertColumn(len(self.fields), fieldname)
        if length:
            self.capture_list.SetColumnWidth(len(self.fields), length)
        self.Layout()


    def update(self, event):
        while self.tshark and len(self.fields) > 0:
            try:
                line = self.tshark.queue.get_nowait()
            except Queue.Empty:
                break

            line = line.strip()
            fields = line.split(",")
            if fields[0]:
                self.update_line(fields)

    def update_line(self, fields):
        self.capture_list.InsertStringItem(self.index, fields[0])
        for i in range(1, len(fields)):
            self.capture_list.SetStringItem(self.index, i, fields[i])

        self.index += 1


    def toggle_capture(self, event):
        if self.tshark:
            self.stop_capture(event)
            self.btn_capture_toggle.SetLabel("Start capture")
        else:
            self.start_capture(event)
            self.btn_capture_toggle.SetLabel("Stop capture")

    def get_device(self):
        device_index = self.devices_list.GetCurrentSelection()
        return self.devices_list.GetItems()[device_index]

    def get_fields(self):
        """To be overridden."""
        return None

    def get_read_filter(self):
        """To be overridden."""
        return None

    def start_capture(self, event=None):
        self.tshark = tshark.TShark(interface=self.get_device(),
                                    fields=self.get_fields(),
                                    separator=',',
                                    read_filter=self.get_read_filter())
        self.tshark.start_capture()
        self.timer.Start(500)

    def stop_capture(self, event=None):
        self.timer.Stop()
        self.tshark.stop_capture()
        self.tshark = None
