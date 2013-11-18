import subprocess

def enumerate():
    """Returns a list of instances of all wireless devices."""
    cmd = "fakeroot airmon-ng | awk '{ print $1 }' | tail -n +5 | head -n -1"
    names = subprocess.check_output(cmd, shell=True).split()
    return map(lambda x: WLAN(x), names)

class WLAN():

    def __init__(self, interface_name):
        self.interface_name = interface_name
        self.is_monitor_mode = False
        self.monitor_mode = None

    def __str__(self):
        return self.interface_name
