from datetime import datetime, timedelta

from email_server.body_parser import EmailMessage

_dupe_queue = {}


def IsDuplicateMessage(message: EmailMessage) -> bool:
    return message.Id in _dupe_queue


def AddSentMessage(message: EmailMessage):
    _dupe_queue[message.Id] = datetime.now() + timedelta(minutes=2)


def ClearExpired():
    for key, value in _dupe_queue.items():
        if datetime.now() > value:
            del _dupe_queue[key]