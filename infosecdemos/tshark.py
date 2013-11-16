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
                 read_filter=None):
        self.interface = interface
        self.fields = fields
        self.separator = separator
        self.read_filter = read_filter
        self.queue = None
        self.queue_thread = None

    def command_line_string(self):
        cmd = ["tshark -n -l"]
        if self.interface:
            cmd.append("-i %s" % self.interface)
        if self.fields:
            cmd.append("-T fields")
            cmd += map(lambda x: "-e %s" % x, self.fields)
            if self.separator:
                cmd.append("-E separator=%s" % self.separator)
        if self.read_filter:
            cmd.append("-R \"%s\"" % self.read_filter)
        return " ".join(cmd)

    def start_capture(self):
        """Starts the process. Can only be called once."""
        print "Starting tshark capture with command:"
        print self.command_line_string()
        subprocess.Popen.__init__(self,
                                  self.command_line_string(),
                                  shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  close_fds=False,
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
