class DummyRequest:
    def __init__(self):
        self.body = None
        self.values = None
        self.files = None

    def set_body(self, body):
        self.body = body
        return self

    def get_json(self, silent=True):
        return self.body

    def set_values(self, values):
        self.values = values
        return self

    def set_files(self, files):
        self.files = files
        return self