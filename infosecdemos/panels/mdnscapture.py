from tsharkpanel import GenericTSharkPanel

class MDNSCapturePanel(GenericTSharkPanel):

    FIELDS = ('eth.addr',
              'dns.qry.name',)
    READ_FILTER = 'udp.srcport == 5353'

    def __init__(self, parent):
        GenericTSharkPanel.__init__(self, parent)
        self.addfield("Device", 50)
        self.addfield("Polling", 500)

    def get_fields(self):
        return MDNSCapturePanel.FIELDS

    def get_read_filter(self):
        return MDNSCapturePanel.READ_FILTER
