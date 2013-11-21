class AccessPointDemo():

    TITLE = "Wifi History"
    MONITOR_MODE = False
    
    TSHARK_FIELDS = ('wlan.sa',
                     'wlan_mgt.ssid subtype probereq',)
    TSHARK_READ_FILTER = 'wlan.fc.type_subtype eq 4'

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

class MACScanDemo():
    TITLE = "Device Scan"
    MONITOR_MODE = True

class Foo():
    TITLE = "Some Other Demo"
    MONITOR_MODE = False
