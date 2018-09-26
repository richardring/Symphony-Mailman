
class InboundMessage:
    def __init__(self, peer, mailfrom, rcpttos, data):
        self.peer = peer
        self.mailfrom = mailfrom
        self.rcpttos = rcpttos
        self.data = data


class MessageAttachment:
    def __init__(self, name, ext, data, mime_type):
        self.Filename = name
        self.Extension = ext
        self.Data = data
        self.MIME = mime_type