import asyncio
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import Envelope, Session, SMTP
from email.message import Message
import spf

import botlog as log
import config
import exceptions
import email_server.exceptions as email_exc
import email_server.email_storage as store
import email_server.email_processor as proc
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

            result, description = spf.check2(ip_address, address, session.host_name)
            log.LogConsoleInfoVerbose('SPF Check [' + ip_address + ', ' + address + ', ' + session.host_name +\
                                      ' ]: ' + result + ' | ' + description)

            valid_spf = result == 'pass'
            envelope.spf = valid_spf

            if config.UseSPFChecking and not valid_spf:
                log.LogSystemErrorVerbose('SPF Check failed - email rejected.')
                return '550 SPF validation failed.'

            if config.UseInboundWhitelist and not whitelist.IsWhitelistedIP(ip_address):
                log.LogSystemErrorVerbose('Whitelist Check failed - email rejected.')
                return '550 Origin blocked.'

            # Check that the user is a valid Symphony user or room
            sender_rcp = proc.ValidateUser(address)

            envelope.mail_from = address
            envelope.mail_options.extend(mail_options)

        except email_exc.SymphonyUserLookupException as user_ex:
            # exceptions.LogException(user_ex)
            log.LogSystemErrorVerbose('Sender is not recognized. Error: ' + str(user_ex))
            return '550 Sender is not recognized. No soup for you.'
        except Exception as ex:
            exceptions.LogException(ex)
            return '500 Unexpected server malfunction'

        return '250 OK'

    async def handle_RCPT(self, server: SMTP, session: Session, envelope: Envelope, address: str, rcpt_options: list):
        rcpt_domain = address.split('@')[1]

        try:
            # reject recipients with domains not found in valid_domains
            if config.ValidDomains and rcpt_domain not in config.ValidDomains:
                log.LogSystemErrorVerbose('Recipient Domain invalid. Recipient rejected.')
                return '550 recipient domain is invalid.'

            # Check that the recipient is a valid Symphony user or room
            rcp = proc.ValidateUser(address)

            # if the recipient is valid, append the address to the envelope recipients list and return OK
            envelope.rcpt_tos.append(address)

        except email_exc.SymphonyUserLookupException as user_ex:
            # exceptions.LogException(user_ex)
            log.LogSystemErrorVerbose('Recipient not found in Symphony. Error: ' + str(user_ex))
            return '554 Recipient not recognized'

        return '250 OK'

    async def handle_DATA(self, server: SMTP, session: Session, envelope: Envelope):
        peer = session.peer
        mail_from = envelope.mail_from
        rcpt_tos = envelope.rcpt_tos
        data = envelope.content  # type: bytes

        # TODO: Possibly implement DKIM here
        # TODO: aiosmtpd provides a Message class to convert the content into email.message.Message
        inbound = InboundMessage(peer, mail_from, rcpt_tos, data)
        log.LogConsoleInfoVerbose('Inbound Email Received: ' + 'From: ' + mail_from + ' || To: ' + str(rcpt_tos))

        try:
            if config.SaveInboundEmail:
                store.SaveInboundEmail(mail_from, data)

            hash_val = hash(data)

            if hash_val not in SentMessages:
                proc.ProcessInboundEmail(inbound)
                SentMessages[hash_val] = True
            else:
                log.LogConsoleInfoVerbose('___---^^^ Duplicate message suppressed ^^^---___')

        except email_exc.SymphonyEmailBodyParseFailedException as mail_ex:
            # exceptions.LogException(mail_ex)
            log.LogSystemErrorVerbose('Email content was unreadable or uninteresting. Error: ' + str(mail_ex))
            return '500 Email content was unreadable or uninteresting.'
        except Exception as ex:
            exceptions.LogException(ex)
            return '500 Could not process your message'

        return '250 OK'


def start_server():
    handler = Hermes_EmailHandler()
    controller = Controller(handler, hostname=config.SMTPServerHost, port=config.SMTPServerPort)

    # Run the event loop in a separate thread
    controller.start()

    # Wait for user to press Return
    # TODO: Create a better handler for exiting from the server
    input('SMTP server is running on dedicated thread. Press Return to stop server and exit. \n\n')
    controller.stop()