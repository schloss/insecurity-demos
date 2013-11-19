import subprocess
import string

def enumerate_interfaces():
    """Returns a list of instances of all wireless devices."""
    # XXX : perhaps use iwconfig, which seems faster than airmon-ng for listing
    cmd = "fakeroot airmon-ng"
    output = subprocess.check_output(cmd, shell=True)
    interfaces = interfaces_from_airmon_ng(output)
    return interfaces

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
        interface = WLAN(*args)
        if len(lines) > 1:
            extra = lines[1].strip(string.whitespace + '()')
            if extra.startswith('monitor mode enabled on'):
                interface.monitor_mode = extra.split()[-1]
        interfaces.append(interface)
    return interfaces

class WLAN():

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
