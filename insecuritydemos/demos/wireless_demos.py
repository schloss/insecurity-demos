class AccessPointDemo():
    TITLE = "Wifi History"
    MONITOR_MODE = True
    WIRELESS_NETWORKS_CONTROL = False
    TSHARK_FIELDS = ('wlan.sa',
                     'wlan_mgt.ssid')
    TSHARK_READ_FILTER = None
    TSHARK_CAPTURE_FILTER = 'subtype probereq'

    def interpret_tshark_output(self, fields):
        out = {}
        if fields and len(fields) == 2 and fields[0]:
            out['mac'] = fields[0]
            probe = fields[1]
            if probe:
                out['aps'] = [{'essid' : probe}]
        return out

class HttpBasicAuthSniffDemo():
    TITLE = "Basic Auth Sniffer"
    MONITOR_MODE = True
    WIRELESS_NETWORKS_CONTROL = True
