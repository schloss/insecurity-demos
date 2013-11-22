import subprocess
import string

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
            # mode, in which case the results from airmon-ng might be
            # for that interface only. The remaining interface lines
            # list other monitor interfaces.  XXX : check this with
            # multiple interfaces available.
            entry = entry.strip("()")
            assert(len(interfaces) == 1)
            interfaces[0].monitor_mode = entry.split()[-1]
            continue
        args = map(lambda x: x.strip(), entry.strip().split('\t'))
        args = filter(None, args)
        interfaces.append(Interface(*args))
    return interfaces

class Interface():

    def __init__(self,
                 interface_name,
                 chipset=None,
                 driver=None,
                 monitor_mode=None):
        self.interface_name = interface_name
        self.chipset = chipset
        self.driver = driver
        self.monitor_mode = monitor_mode

    def enable_monitor_mode(self):
        cmd = "airmon-ng start %s" % self.interface_name
        output = subprocess.check_output(cmd, shell=True)
        results = interfaces_from_airmon_ng(output)
        assert(results)
        interface = results[0]
        assert(interface.interface_name == self.interface_name)
        assert(interface.monitor_mode)
        self.monitor_mode = interface.monitor_mode

    def disable_monitor_mode(self):
        if not self.monitor_mode:
            return
        cmd = "airmon-ng stop %s" % self.monitor_mode
        lines = subprocess.check_output(cmd, shell=True).splitlines()
        # Verify that the interface was indeed taken out of monitor mode.
        for x in lines:
            if x.startswith(self.monitor_mode) and x.endswith("(removed)"):
                self.monitor_mode = None
                break
        else:
            print "Oops: Something unexpected happened."
            print ("Could not verify that %s was taken out of monitor mode."
                   % self.interface_name)

    def __str__(self):
        return self.interface_name

    def __repr__(self):
        out = ['interface name: %s' % self.interface_name]
        if self.chipset:
            out.append('chipset: %s' % self.chipset)
        if self.driver:
            out.append('driver: %s' % self.driver)
        if self.monitor_mode:
            out.append('monitor mode on: %s' % self.monitor_mode)
        return '\n'.join(out)

class Network():

    def __init__(self,
                 essid,
                 bssid=None,
                 channel=None,
                 security=None):
        self.essid = essid
        self.bssid = bssid
        self.channel = channel
        self.security = security

    def __str__(self):
        return "%s (%s)" % (self.essid, self.bssid)

class User():

    def __init__(self,
                 mac=None,
                 hardware=None,
                 nickname=None,
                 ip=None,
                 aps=None):
        self.mac = mac
        self.hardware = hardware
        self.nickname = nickname
        self.ip = ip
        self.aps = aps or []
