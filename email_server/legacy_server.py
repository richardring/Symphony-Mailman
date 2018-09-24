import asyncore

from smtpd import SMTPServer, DebuggingServer

import botlog as log
import config
import exceptions
import email_server.email_storage as store
import email_server.email_processor as proc
from email_server.models import InboundMessage


class EmailServer(SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        inbound = InboundMessage(peer, mailfrom, rcpttos, data)
        log.LogConsoleInfoVerbose('Inbound Email Received: ' + 'From: ' + mailfrom + ' || To: ' + str(rcpttos))

        try:
            if config.SaveInboundEmail:
                store.SaveInboundEmail(mailfrom, data)

            proc.ProcessInboundEmail(inbound)

        except Exception as ex:
            exceptions.LogException(ex)


def start_server():
    log.LogConsoleInfo('Starting legacy SMTP server. Press CTRL+C to quit.')

    if config.UseDebuggingServer:
        server = DebuggingServer((config.SMTPDebugHost, config.SMTPDebugPort), None)
    else:
        server = EmailServer((config.SMTPServerHost, config.SMTPServerPort), None)

    try:
        asyncore.loop()
    except KeyboardInterrupt:
        log.LogConsoleInfo('Closing server')
