from tsharkpanel import GenericTSharkPanel

class HTTPCapturePanel(GenericTSharkPanel):
    def __init__(self, parent):
        GenericTSharkPanel.__init__(self,
                                    parent,
                                    "-e http.request.method -e http.host \
                                    -e http.request.uri -e http.response.code \
                                    -R 'http'")
        self.addfield("Method", 50)
        self.addfield("Domain", 250)
        self.addfield("URL", 500)
        self.addfield("Status", 50)
