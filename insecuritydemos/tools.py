import os
import random
import string
import subprocess
from threading import Thread
from Queue import Queue, Empty

def _enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

class TShark(subprocess.Popen):
    """A Pythonic wrapper around the TShark command-line utility."""

    def __init__(self,
                 interface=None,
                 fields=None,
                 separator=None,
                 capture_filter=None,
                 read_filter=None,
                 preferences=None):
        self.interface = interface
        self.fields = fields
        self.separator = separator
        self.capture_filter = capture_filter
        self.read_filter = read_filter
        self.preferences = preferences
        self.queue = None
        self.queue_thread = None

    def command_line_string(self):
        cmd = ["tshark -2 -n -l"]
        if self.interface:
            cmd.append("-i %s" % self.interface)
        if self.preferences:
            cmd += map(lambda x: "-o \"%s\"" % x, self.preferences)
        if self.fields:
            cmd.append("-T fields")
            cmd += map(lambda x: "-e %s" % x, self.fields)
            if self.separator:
                cmd.append("-E separator=%s" % self.separator)
        if self.read_filter:
            cmd.append("-R \"%s\"" % self.read_filter)
        if self.capture_filter:
            cmd.append("-f \"%s\"" % self.capture_filter)
        return " ".join(cmd)

    def start_capture(self):
        """Starts the process. Can only be called once."""
        cmd = self.command_line_string()
        print "Starting tshark capture with command:\n%s" % cmd
        subprocess.Popen.__init__(self,
                                  cmd,
                                  shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  close_fds=True,
                                  bufsize=500)
        self.queue = Queue()
        self.queue_thread = Thread(target=_enqueue_output,
                                   args=(self.stdout, self.queue))
        self.queue_thread.daemon = True
        self.queue_thread.start()
        print "...tshark started."

    def stop_capture(self):
        """Stops the process. Can only be called once."""
        print "Stopping tshark..."
        self.terminate()
        self.kill()
        print "...tshark stopped."

class Airodump(subprocess.Popen):
    """A Pythonic wrapper around the airodump command-line utility."""

    def __init__(self, interface=None):
        self.interface = interface
        alphabet = string.ascii_uppercase + string.digits
        base = ''.join([random.choice(alphabet) for x in range(16)])
        self.prefix = os.path.join('/', 'tmp', base)
        self.temp_filename = "%s-01.csv" % self.prefix

    def command_line_string(self):
        cmd = ["airodump-ng"]
        cmd.append("-w %s" % self.prefix)
        cmd.append("--output-format=csv")
        if self.interface:
            cmd.append(self.interface)
        return " ".join(cmd)

    def start_capture(self):
        """Starts the process. Can only be called once."""
        cmd = self.command_line_string()
        print "Starting airodump with command:\n%s" % cmd
        subprocess.Popen.__init__(self,
                                  cmd,
                                  shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  close_fds=True,
                                  bufsize=500)
        self.queue = Queue()
        self.queue_thread = Thread(target=_enqueue_output,
                                   args=(self.stdout, self.queue))
        self.queue_thread.daemon = True
        self.queue_thread.start()
        print "...airodump started."

    def stop_capture(self):
        """Stops the process. Can only be called once."""
        print "Stopping airodump..."
        self.terminate()
        self.kill()
        print "...airodump stopped."

    def status(self):
        f = open(self.temp_filename, 'r')
        lines = f.readlines()
        f.close()

        if not lines:
            print "airodump has no data"
            return [], []

        # Find breaks between tables.
        breakline = '\r\n'
        first = lines.index(breakline)
        second =  lines.index(breakline, first + 1)
        third = lines.index(breakline, second + 1)
        assert first == 0
        assert third == len(lines) - 1
        ap_lines = lines[1:second]
        client_lines = lines[second+1:third]

        # Parse table of APs.
        ap_header = ("BSSID, First time seen, Last time seen, channel, "
                     "Speed, Privacy, Cipher, Authentication, Power, "
                     "# beacons, # IV, LAN IP, ID-length, ESSID, Key")
        assert ap_lines.pop(0).strip() == ap_header
        ap_header = [x.strip() for x in ap_header.split(',')]
        bssid_index = ap_header.index("BSSID")
        channel_index = ap_header.index("channel")
        security_index = ap_header.index("Privacy")
        essid_index = ap_header.index("ESSID")
        aps = {}
        for line in ap_lines:
            ap = [x.strip() for x in line.split(',')]
            bssid = ap[bssid_index]
            aps[bssid] = {'essid': ap[essid_index],
                          'bssid': bssid,
                          'channel': ap[channel_index],
                          'security': ap[security_index]}

        # Parse table of clients.
        client_header = ("Station MAC, First time seen, Last time seen, "
                         "Power, # packets, BSSID, Probed ESSIDs")
        assert client_lines.pop(0).strip() == client_header
        client_header = [x.strip() for x in client_header.split(',')]
        bssid_index = client_header.index('BSSID')
        mac_index = client_header.index('Station MAC')
        clients = []
        for line in client_lines:
            client = [x.strip() for x in line.split(',')]
            bssid = client[bssid_index]
            clients.append({'mac': client[mac_index],
                            'current_network': aps.get(bssid, None)})

        return aps.values(), clients
