import os
import string
import subprocess

OUI_FILE_PATH = '/usr/share/aircrack-ng/airodump-ng-oui.txt'
MAC_HARDWARE = {}

def force_deauthentication(ap_mac, target_mac, interface):
    """Using the given interface, actively bumps a target MAC from the
    given network, forcing the device to re-authenticate."""
    cmd = "aireplay-ng -0 1 -a %s -c %s %s" % (ap_mac, target_mac, interface)
    print "Forcing deauthentication: %s" % cmd
    output = subprocess.check_output(cmd, shell=True)
    print "Output: %s" % output

def enumerate_networks(interface):
    """Returns a list of all wireless networks found by the given interface."""
    if not interface:
        return None
    interface = str(interface)
    cmd = "iwlist %s scan" % interface
    try:
        output = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError:
        print "Oops: Something is wrong with the network interface."
        print "To fix it, try running this command:"
        print ("sudo ifconfig %s down && sudo ifconfig %s up" %
               (interface, interface))
        return []
    result = output.split('\n', 1)[0].replace(' ','')
    if result == ("%sScancompleted:" % interface):
        return networks_from_iwlist(output)
    elif result == ("%sNoscanresults" % interface):
        return []
    print "Oops: Something unexpected happened when running this command:"
    print "      " + cmd
    print "      the output of which was:"
    print "************************************"
    print output
    print "************************************"
    return []

def enumerate_interfaces():
    """Returns a list of all wireless networking interfaces found on
    the local host."""
    # XXX : perhaps use iwconfig, which seems faster than airmon-ng for listing
    cmd = "fakeroot airmon-ng"
    output = subprocess.check_output(cmd, shell=True)
    interfaces = interfaces_from_airmon_ng(output)
    return interfaces

def networks_from_iwlist(blob):
    offset = blob.index("Scan completed :")
    cells = blob.split('\n' + offset*' ' + 'Cell')[1:]
    networks = []
    for cell in cells:
        if not cell:
            continue
        lines = cell.split('\n')
        lines[0] = lines[0].split(' - ')[1] # Remove cell number.
        essid = None
        bssid = None
        channel = None
        security = []
        for line in lines:
            line = line.strip(string.whitespace)
            if line.startswith("Address:"):
                bssid = line[len("Address:"):].strip(string.whitespace)
            elif line.startswith("ESSID:"):
                essid = line[len("ESSID:"):].strip(string.whitespace + '"')
            elif line.startswith("Channel:"):
                channel = line[len("Channel:"):].strip(string.whitespace)
            elif line.startswith("IE:"):
                sec = line[len("IE:"):].strip(string.whitespace)
                if not sec.startswith("Unknown:"):
                    security.append(sec)
        if essid:
            networks.append(Network(essid, bssid, channel, security))
    return networks

def interfaces_from_airmon_ng(blob):
    MONITOR_MODE_FLAG = '(monitor mode enabled on'
    blocks = map(lambda x: x.strip(), blob.split('\n\n'))
    for i, block in enumerate(blocks):
        if block.startswith("Interface"):
            block = block.replace('\t','')
            if block == "InterfaceChipsetDriver":
                interface_lines = blocks[i+1].splitlines()
                break
    else:
        interface_lines = []
    interface_lines = filter(None, interface_lines)
    interfaces = []
    for entry in interface_lines:
        entry = entry.strip()
        if entry.startswith(MONITOR_MODE_FLAG):
            # This only happens when an interface is put into monitor
            # mode.
            entry = entry.strip("()")
            assert(len(interfaces) > 0)
            interfaces[-1].monitor_mode = entry.split()[-1]
            continue
        args = map(lambda x: x.strip(), entry.strip().split('\t'))
        args = filter(None, args)
        interfaces.append(Interface(*args))
    return interfaces

def has_oui_database():
    return os.path.isfile(OUI_FILE_PATH)

def update_oui_database():
    os.system("airodump-ng-oui-update")

def hardware_from_mac(mac):
    if len(MAC_HARDWARE) == 0:
        if os.path.isfile(OUI_FILE_PATH):
            f = open(OUI_FILE_PATH, 'r')
            for line in f:
                segments = line.strip().split('\t')
                prefix = segments[0].split()[0].replace('-',':').upper()
                hardware = segments[-1]
                MAC_HARDWARE[prefix] = hardware
        else:
            print ("Oops: the OUI file doesn't exist in the expected "
                   "location (%s)" % OUI_FILE_PATH)
            return None
    prefix = mac[0:8].upper()
    return MAC_HARDWARE.get(prefix, None)

def obscure_text(text):
    x = len(text)
    if x > 7:
        return text[:3] + "*"*(x-6) + text[-3:]
    elif x > 2:
        return text[0] + "*"*(x-2) + text[-1]
    else:
        return "*"*x

class Interface():

    def __init__(self,
                 name,
                 chipset=None,
                 driver=None,
                 monitor_mode=None,
                 monitor_mode_channel=None):
        self.name = name
        self.chipset = chipset
        self.driver = driver
        self.monitor_mode = monitor_mode
        self.monitor_mode_channel = monitor_mode_channel

    def enable_monitor_mode(self, channel=None):
        if self.monitor_mode:
            print ("Interface %s already in monitor mode on channel %s." %
                   (self.name, self.monitor_mode_channel))
            return
        cmd = "airmon-ng start %s %s" % (self.name, channel or '')
        print "Entering monitor mode: %s" % cmd
        output = subprocess.check_output(cmd, shell=True)
        results = interfaces_from_airmon_ng(output)
        assert(results)
        for interface in results:
            if interface.name == self.name:
                assert(interface.monitor_mode)
                self.monitor_mode = interface.monitor_mode
                self.monitor_mode_channel = channel
                break
        else:
            print "Oops: Something unexpected happened."
            print ("Could not verify that the %s interface is "
                   "in monitor mode." % self.name)

    def disable_monitor_mode(self):
        if not self.monitor_mode:
            return
        cmd = "airmon-ng stop %s" % self.monitor_mode
        print "Leaving monitor mode: %s" % cmd
        lines = subprocess.check_output(cmd, shell=True).splitlines()
        # Verify that the interface was indeed taken out of monitor mode.
        for x in lines:
            if x.startswith(self.monitor_mode) and x.endswith("(removed)"):
                self.monitor_mode = None
                self.monitor_mode_channel = None
                break
        else:
            print "Oops: Something unexpected happened."
            print ("Could not verify that %s was taken out of monitor mode."
                   % self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        out = ['interface name: %s' % self.name]
        if self.chipset:
            out.append('chipset: %s' % self.chipset)
        if self.driver:
            out.append('driver: %s' % self.driver)
        if self.monitor_mode:
            out.append('monitor mode on: %s' % self.monitor_mode)
        return '\n'.join(out)

class Network():

    def __init__(self,
                 essid=None,
                 bssid=None,
                 channel=None,
                 security=None,
                 password=None):
        self.essid = essid
        self.bssid = bssid
        self.channel = channel
        self.security = security
        self.password = password
        if self.bssid:
            self.bssid = self.bssid.upper()

    def __le__(self, x):
        if not self.essid:
            return -1
        return self.essid.__le__(x.essid)

    def __gt__(self, x):
        if not self.essid:
            return 1
        return self.essid.__gt__(x.essid)

    def __eq__(self, x):
        if not isinstance(x, Network):
            return False
        if not self.essid:
            return False
        return self.essid.__eq__(x.essid)

    def __str__(self):
        return "%s (%s)" % (self.essid, self.bssid)

    def __repr__(self):
        return ("Network(essid=%s, bssid=%s, channel=%s, "
                "security=%s, password=%s)" %
                (self.essid, self.bssid, self.channel,
                 self.security, self.password))

    def export(self):
        return {"essid": self.essid,
                "bssid": self.bssid,
                "channel": self.channel,
                "security": self.security,
                "password": self.password}

    def merge(self, network):
        self.essid = self.essid or network.essid
        self.bssid = self.bssid or network.bssid
        self.channel = self.channel or network.channel
        self.security = self.security or network.security
        self.password = self.password or network.password

class Credential():

    SEPARATOR = ":"

    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password

    def __le__(self, x):
        return self.username.__le__(x.username)

    def __gt__(self, x):
        return self.username.__gt__(x.username)

    def __eq__(self, x):
        return self.username.__eq__(x.username)

    def __str__(self):
        return "%s%s%s" % (self.username, self.SEPARATOR, self.password)

    def export(self):
        return {'username': self.username,
                'password': self.password}

    @staticmethod
    def from_string(s):
        username, password = s.split(Credential.SEPARATOR, 1)
        return Credential(username, password)

class User(object):

    def __init__(self,
                 mac=None,
                 hardware=None,
                 nickname=None,
                 ip=None,
                 hostname=None,
                 current_network=None,
                 aps=None,
                 anonymous_aps=True,
                 credentials=None,
                 anonymous_creds=True,
                 eapol_flags=0):
        self.mac = mac
        if self.mac:
            self.mac = self.mac.upper()
        self.hardware = hardware
        if self.mac and not self.hardware:
            self.hardware = hardware_from_mac(self.mac)
        self.nickname = nickname
        self.ip = ip
        self.hostname = hostname
        self.current_network = current_network
        if type(self.current_network) == dict:
            self.current_network = Network(**self.current_network)
        self.aps = aps or []
        if all([type(x) == dict for x in self.aps]):
            self.aps = [Network(**x) for x in self.aps]
        self.aps.sort()
        self.anonymous_aps = anonymous_aps
        self.credentials = credentials or []
        if all([type(x) in (str, unicode) for x in self.credentials]):
            self.credentials = map(Credential.from_string, self.credentials)
        elif all([type(x) == dict for x in self.credentials]):
            self.credentials = [Credential(**x) for x in self.credentials]
        self.credentials.sort()
        self.anonymous_creds = anonymous_creds
        self.eapol_flags = eapol_flags
        self.sniffable = False

    def merge(self, user):
        self.mac = self.mac or user.mac
        self.hardware = self.hardware or user.hardware
        self.nickname = user.nickname or self.nickname
        self.ip = user.ip or self.ip
        self.hostname = user.hostname or self.hostname
        for ap in user.aps:
            if ap not in self.aps:
                self.aps.append(ap)
        self.aps.sort()
        for credential in user.credentials:
            if credential not in self.credentials:
                self.credentials.append(credential)
        self.credentials.sort()
        self.current_network = user.current_network or self.current_network
        self.eapol_flags |= user.eapol_flags
        self.sniffable = (self.eapol_flags == 0b1111)
        # Don't change the anonymity of this user.

    def export(self):
        """Returns a dict containing all data that should be persisted."""
        return {'mac': self.mac,
                'hardware': self.hardware,
                'nickname': self.nickname,
                'ip': self.ip,
                'hostname': self.hostname,
                'aps': [x.export() for x in self.aps],
                'anonymous_aps': self.anonymous_aps,
                'credentials': [x.export() for x in self.credentials],
                'anonymous_creds': self.anonymous_creds}

    def nickname_to_string(self):
        return self.nickname or ''

    def nickname_from_string(self, x):
        self.nickname = x or None
        return self.nickname

    def aps_to_string(self, joiner=', '):
        if self.anonymous_aps:
            seq = [obscure_text(x.essid) for x in self.aps]
        else:
            seq = [x.essid for x in self.aps]
        return joiner.join(seq)

    def credentials_to_string(self, joiner=', '):
        if self.anonymous_creds:
            seq = [Credential.SEPARATOR.join((obscure_text(x.username),
                                              obscure_text(x.password))) \
                   for x in self.credentials]
        else:
            seq = map(str, self.credentials)
        return joiner.join(seq)

    def current_network_to_string(self):
        if self.current_network:
            return (self.current_network.essid or
                    "[%s]" % self.current_network.bssid)
        else:
            return ''
