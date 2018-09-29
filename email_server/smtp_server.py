import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import Envelope, Session, SMTP
from email.message import Message
import spf
import time

import botlog as log
import config
import exceptions
import email_server.exceptions as email_exc
import email_server.email_storage as store
import email_server.email_processor as proc
import email_server.integrity as dupe_c
import email_server.whitelist as whitelist
from email_server.models import InboundMessage

SentMessages = {}


# SMTP Reply Codes: https://www.greenend.org.uk/rjk/tech/smtpreplies.html
# aiosmtpd handlers: https://aiosmtpd.readthedocs.io/en/latest/aiosmtpd/docs/handlers.html
class Hermes_EmailHandler:
    async def handle_EHLO(self, server: SMTP, session: Session, envelope: Envelope, hostname: str):
        log.LogConsoleInfoVerbose('EHLO Received from ' + hostname)
        session.host_name = hostname
        return '250 HELP'

    # SPF implementation found here: https://github.com/denself/simple_mail_server
    async def handle_MAIL(self, server: SMTP, session: Session, envelope: Envelope, address: str, mail_options: list):
        try:
            ip_address = session.peer[0]

            if not proc.VerifySymphonyConnection():
                return '421 Symphony is currently unavailable. Try again later.'

            if config.UseSPFChecking:
                result, description = spf.check2(ip_address, address, session.host_name)
                log.LogConsoleInfoVerbose('SPF Check [' + ip_address + ', ' + address + ', ' + session.host_name +
                                          ' ]: ' + result + ' | ' + description)

                valid_spf = result == 'pass'
                envelope.spf = valid_spf

                if not valid_spf:
                    log.LogSystemErrorVerbose('SPF Check failed - email rejected.')
                    return '550 SPF validation failed.'
            else:
                envelope.spf = True

            if config.UseInboundWhitelist and not whitelist.IsWhitelistedIP(ip_address):
                log.LogSystemErrorVerbose('Whitelist Check failed - email rejected.')
                return '550 Origin blocked.'

            # Check that the user is a valid Symphony user or room
            log.LogSystemInfoVerbose('SMTP MAIL: Checking sender(' + address + ') is valid...')
            sender_rcp = proc.ValidateUser(address)

            envelope.mail_from = address
            envelope.mail_options.extend(mail_options)

        except email_exc.SymphonyUserLookupException as user_ex:
            log.LogSystemErrorVerbose('Sender is not recognized. Error: ' + str(user_ex))
            return '550 Sender is not recognized.'
        except Exception as ex:
            exceptions.LogException(ex)
            return '500 Unexpected server malfunction'

        return '250 OK'

    async def handle_RCPT(self, server: SMTP, session: Session, envelope: Envelope, address: str, rcpt_options: list):
        rcpt_domain = address.split('@')[1]

        log.LogSystemInfoVerbose('SMTP RCPT: Verifying recipient (' + address + ')')
        log.LogSystemInfoVerbose('SMTP RCPT: Recipient verification is disabled.')

        try:
            # reject recipients with domains not found in valid_domains
            if config.ValidDomains and rcpt_domain not in config.ValidDomains:
                log.LogSystemErrorVerbose('Recipient Domain invalid. Recipient rejected.')
                return '550 recipient domain is invalid.'

            # Check that the recipient is a valid Symphony user or room
            # if the recipient is valid, append the address to the envelope recipients list and return OK
            # if proc.ValidateUser(address):

            envelope.rcpt_tos.append(address)

        except email_exc.SymphonyUserLookupException as user_ex:
            exceptions.LogException(user_ex, 'Recipient not found in Symphony.')
            # return '554 Recipient not recognized'

        return '250 OK'

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        log.LogSystemInfoVerbose('SMTP DATA: Processing inbound email message.')
        peer = session.peer
        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        data = envelope.content  # type: bytes

        # TODO: Possibly implement DKIM here
        inbound = InboundMessage(peer, mail_from, rcpt_tos, data)

        try:
            if config.SaveInboundEmail:
                store.SaveInboundEmail(mail_from, data)

            proc.ProcessInboundEmail(inbound)

        except email_exc.SymphonyEmailBodyParseFailedException as mail_ex:
            exceptions.LogException(mail_ex, 'Email content was unreadable or uninteresting.')
            return '500 Email content was unreadable or uninteresting.'
        except Exception as ex:
            exceptions.LogException(ex)
            return '500 Could not process your message'

        return '250 OK'


def start_server():
    handler = Hermes_EmailHandler()
    controller = Controller(handler, hostname=config.SMTPServerHost, port=config.SMTPServerPort)
    heartbeat_index = 1

    try:
        # Run the event loop in a separate thread
        log.LogSystemInfo('Starting SMTP server on dedicated thread...')
        controller.start()

        while True:
            time.sleep(60)
            heartbeat_index += 1

            dupe_c.ClearExpired()

            if heartbeat_index == 30:
                log.LogSystemInfoVerbose('Heartbeat...ba-dump...')
                heartbeat_index = 0

        # TODO: Create a better handler for exiting from the server
        # controller.stop()
    except Exception as ex:
        exceptions.LogException(ex)
    finally:
        log.LogSystemInfo('Stopping SMTP server...')
        # controller.stop()
