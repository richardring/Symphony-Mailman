class SymphonyUserLookupException(Exception):
    def __init__(self, message):
        super().__init__('User Lookup Failed: ' + message)


class SymphonyEmailBodyParseFailedException(Exception):
    def __init__(self, message):
        super().__init__('Email Parsing Failed: ' + message)
