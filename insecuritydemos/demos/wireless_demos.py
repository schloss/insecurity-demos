class AccessPointDemo():
    TITLE = "Wifi History"
    MONITOR_MODE = True
    REQUIRES_NETWORK = False
    REQUIRES_NETWORK_PASSWORD = False
    TSHARK_FIELDS = ['wlan.sa', 'wlan_mgt.ssid', 'wlan.bssid']
    TSHARK_READ_FILTER = None
    TSHARK_CAPTURE_FILTER = 'subtype probereq or type data'
    TSHARK_SUPPLY_PASSWORD = False
    TSHARK_PREFERENCES = []

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
    REQUIRES_NETWORK = True
    REQUIRES_NETWORK_PASSWORD = True
    TSHARK_FIELDS = ["eapol.keydes.key_info",
                     "wlan.sa",
                     "wlan.da",
                     "ip.src",
                     "dns.ptr.domain_name",
                     "wlan_mgt.ssid",
                     "wlan.bssid",
                     "http.authbasic"]
    TSHARK_READ_FILTER = None
    TSHARK_CAPTURE_FILTER = ("type data or "
                             "ether proto 0x888e or "
                             "subtype probereq or "
                             "udp src port 5353")
    TSHARK_SUPPLY_PASSWORD = True
    TSHARK_PREFERENCES = ["wlan.enable_decryption:TRUE"]

    def interpret_tshark_output(self, fields):
        if len(fields) == len(self.TSHARK_FIELDS):
            if fields[0]:
                key_info = fields[0]
                if key_info == "0x008a":
                    message_id = 1
                elif key_info == "0x010a":
                    message_id = 2
                elif key_info == "0x13ca":
                    message_id = 3
                elif key_info == "0x030a":
                    message_id = 4
                else:
                    print "UNKNOWN EAPOL KEY INFO:", fields
                    return None
                if message_id in (1, 3):
                    user_mac = fields[2]
                    ap_mac = fields[1]
                elif message_id in (2, 4):
                    user_mac = fields[1]
                    ap_mac = fields[2]
                return {'mac': user_mac,
                        'current_network': {'bssid': ap_mac},
                        'eapol_flags': 1 << (message_id - 1)}
            else:
                user = {'mac': fields[1],
                        'ip': fields[3] or None}
                if fields[4]:
                    raw_hostname = fields[4]
                    hostnames = [x.strip() for x in raw_hostname.split(',')]
                    suffix = ".local"
                    s = set()
                    for x in hostnames:
                        if x.endswith(suffix):
                            s.add(x[:-len(suffix)])
                        else:
                            s.add(x)
                    user['hostname'] = ", ".join(list(s).sort())
                if fields[5] or fields[6]:
                    user['current_network'] = {'essid': fields[5] or None,
                                               'bssid': fields[6] or None}
                if fields[7]:
                    username, password = fields[7].split(':')
                    user["credentials"] = [{"username": username,
                                           "password": password}]
                return user
        print "UNKNOWN TSHARK FIELDS:", fields
        return None
