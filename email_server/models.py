
class InboundMessage:
    def __init__(self, peer, mailfrom, rcpttos, data):
        self.peer = peer
        self.mailfrom = mailfrom
        self.rcpttos = rcpttos
        self.data = data


class MessageAttachment:
    def __init__(self, name: str=None, ext: str=None, data=None, mime_type:str=None):
        self.Filename = name
        self.Extension = ext
        self.Data = data
        self.MIME = mime_type