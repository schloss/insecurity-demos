import re

HEX_BYTE_RE = r'[\da-fA-F][\da-fA-F]'
MAC_RE = ':'.join(6*[HEX_BYTE_RE])

class AccessPointDemo():
    TITLE = "Wifi History"
    MONITOR_MODE = True
    WIRELESS_NETWORKS_CONTROL = False
    REQUIRES_NETWORK = False
    REQUIRES_NETWORK_PASSWORD = False
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
    REQUIRES_NETWORK = True
    REQUIRES_NETWORK_PASSWORD = True
    TSHARK_FIELDS = []
    TSHARK_READ_FILTER = 'eapol'
    TSHARK_CAPTURE_FILTER = None

    EAPOL_RE = re.compile(r'[\d.]+ (?P<from>' +
                          MAC_RE +
                          r') -> (?P<to>' +
                          MAC_RE +
                          r') EAPOL \d+ Key \(Message (?P<msg>[1-4]) of 4\)')

    def interpret_tshark_output(self, fields):
        if len(fields) == 1:
            match = self.EAPOL_RE.search(fields[0])
            if match:
                message_id = int(match.group('msg'))
                if message_id in (1, 3):
                    user_mac = match.group('to')
                    ap_mac = match.group('from')
                elif message_id in (2, 4):
                    user_mac = match.group('from')
                    ap_mac = match.group('to')
                return {'mac': user_mac,
                        'current_network': {'bssid': ap_mac},
                        'eapol_flags': 1 << (message_id - 1)}
        print "UNKNOWN TSHARK FIELDS:", fields
        return None
