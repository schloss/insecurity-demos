class AccessPointDemo():
    TITLE = "Wifi History"
    MONITOR_MODE = True
    WIRELESS_NETWORKS_CONTROL = False
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
    WIRELESS_NETWORKS_CONTROL = True
    REQUIRES_NETWORK = True
    REQUIRES_NETWORK_PASSWORD = True
    TSHARK_FIELDS = ["eapol",
                     "eapol.keydes.key_info",
                     "wlan.sa",
                     "wlan.da",
                     "ip.src",
                     "http.authbasic"]
    TSHARK_READ_FILTER = "http.authbasic || eapol"
    TSHARK_CAPTURE_FILTER = None
    TSHARK_SUPPLY_PASSWORD = True
    TSHARK_PREFERENCES = ["wlan.enable_decryption:TRUE"]

    def interpret_tshark_output(self, fields):
        if len(fields) == len(self.TSHARK_FIELDS):
            if fields[0] == "eapol":
                key_info = fields[1]
                if key_info == "0x008a":
                    message_id = 1
                elif key_info == "0x010a":
                    message_id = 2
                elif key_info == "0x13ca":
                    message_id = 3
                elif key_info == "0x030a":
                    message_id = 4
                else:
                    if key_info:
                        print "UNKNOWN EAPOL KEY INFO:", fields
                    return None
                if message_id in (1, 3):
                    user_mac = fields[3]
                    ap_mac = fields[2]
                elif message_id in (2, 4):
                    user_mac = fields[2]
                    ap_mac = fields[3]
                return {'mac': user_mac,
                        'current_network': {'bssid': ap_mac},
                        'eapol_flags': 1 << (message_id - 1)}
            else:
                user = {'mac': fields[2]}
                if fields[4]:
                    user["ip"] = fields[4]
                if fields[5]:
                    username, password = fields[5].split(':')
                    user["credentials"] = [{"username": username,
                                           "password": password}]
                return user
        print "UNKNOWN TSHARK FIELDS:", fields
        return None
