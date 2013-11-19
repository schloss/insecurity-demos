from tsharkpanel import GenericTSharkPanel

class HTTPCapturePanel(GenericTSharkPanel):

    title = "Pages Visited"
    monitor_mode = False
    FIELDS = ('http.request.method',
              'http.host',
              'http.request.uri',
              'http.response.code',)
    READ_FILTER = 'http'

    def __init__(self, parent):
        GenericTSharkPanel.__init__(self, parent)
        self.addfield("Method", 50)
        self.addfield("Domain", 250)
        self.addfield("URL", 500)
        self.addfield("Status", 50)

    def get_fields(self):
        return HTTPCapturePanel.FIELDS

    def get_read_filter(self):
        return HTTPCapturePanel.READ_FILTER
