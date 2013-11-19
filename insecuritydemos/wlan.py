import subprocess
import string

def enumerate_networks(interface):
    """Returns a list of all wireless networks found by the given interface."""
    if not interface:
        return None
    interface = str(interface)
    cmd = "iwlist %s scan" % interface
    output = subprocess.check_output(cmd, shell=True)
    assert(output.split('\n')[0].replace(' ','') ==
           ("%sScancompleted:" % interface))
    networks = networks_from_iwlist(output)
    return networks

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
    blocks = map(lambda x: x.strip(), blob.split('\n\n'))
    for i, block in enumerate(blocks):
        if block.startswith("Interface"):
            block = block.replace('\t','')
            if block == "InterfaceChipsetDriver":
                interface_lines = blocks[i+1].split('\n')
                break
    else:
        interface_lines = []
    interface_lines = filter(None, interface_lines)
    interfaces = []
    for entry in interface_lines:
        lines = entry.split('\n')
        args = map(lambda x: x.strip(), lines[0].strip().split('\t'))
        args = filter(None, args)
        interface = Interface(*args)
        if len(lines) > 1:
            extra = lines[1].strip(string.whitespace + '()')
            if extra.startswith('monitor mode enabled on'):
                interface.monitor_mode = extra.split()[-1]
        interfaces.append(interface)
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
        print "Enabling monitor mode:"
        print cmd
        output = subprocess.check_output(cmd, shell=True)
        print output
        # XXX : should actually check that it worked

    def disable_monitor_mode(self):
        cmd = "airmon-ng stop %s" % self.interface_name
        print "Disabling monitor mode:"
        print cmd
        lines = subprocess.check_output(cmd, shell=True)
        print lines
        # XXX : should actually check that it worked

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
