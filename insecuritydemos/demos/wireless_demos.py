class AccessPointDemo():
    TITLE = "Wifi History"
    MONITOR_MODE = True
    WIRELESS_NETWORKS_CONTROL = False
    TSHARK_FIELDS = ('wlan.sa',
                     'wlan_mgt.ssid',
                     'wlan.bssid')
    TSHARK_READ_FILTER = None
    TSHARK_CAPTURE_FILTER = 'subtype probereq or type data'

    def interpret_tshark_output(self, fields):
        out = {}
        if fields and len(fields) == 3 and fields[0]:
            out['mac'] = fields[0]
            probe = fields[1]
            if probe:
                out['aps'] = [{'essid' : probe}]
            ap = fields[2]
            if ap and ap != 'ff:ff:ff:ff:ff:ff':
                out['current_network'] = {'bssid' : ap}
        return out

class HttpBasicAuthSniffDemo():
    TITLE = "Basic Auth Sniffer"
    MONITOR_MODE = True
    WIRELESS_NETWORKS_CONTROL = True
