import wx
from tsharkpanel import GenericTSharkPanel

class WLANProbesPanel(GenericTSharkPanel):
    def __init__(self, parent):
        GenericTSharkPanel.__init__(self,
                                    parent,
                                    "-R 'wlan.fc.type_subtype eq 4' -e wlan.sa \
                                    -e wlan_mgt.ssid subtype probereq")
        self.addfield("Device", 80)
        self.addfield("Polling", 600)
        # self.capture_list.Bind(wx.wxEVT_LEFT_DCLICK, self.showdetails)

    def showdetails(self, event):
        selected = self.capture_list.GetFirstSelected()
        if selected < 0:
            return

        item = self.capture_list.GetItem(selected)
        print item


    def update_line(self, fields):
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
