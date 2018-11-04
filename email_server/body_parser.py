# https://docs.python.org/3/library/email.examples.html
from email import message as email_message
from email import policy
# from email.iterators import _structure
from email.parser import BytesParser
import mimetypes
import os
import uuid

import config
import email_server.models as models
import email_server.user_matching as users
import exceptions as exc
import email_server.utility as util


def ParseEmailMessage(email_data):
    # BytesParser(policy) is required to expose the .get_body() method.
    return EmailMessage(BytesParser(policy=policy.default).parsebytes(email_data))


class EmailMessage:
    def __init__(self, parsed_message: email_message):
        self.From = parsed_message['from']
        self.To = parsed_message['to']
        self.CC = parsed_message['cc']
        self.FromEmail = ''
        self.ToEmailList = []
        self.CCEmailList = []
        self.RecipientList = []
        self.FromUser = None
        self.ToUsers = []
        self.CCUsers = []
        self.Subject = parsed_message['subject']
        self.Body_Text = None
        self.Body_HTML_Raw = None
        self.Body_MML = None
        self.Attachments = []
        self.IsValid = True
        self.MessageId = ''
        self.PrimaryBoundary = ''

        self.ParseEmailAddresses()
        self.UserLookup()
        self.ParseEmailContent(parsed_message)
        self.CreateMessageML()

        self.Id = util.CreateUniqueId(self)

    def UserLookup(self):
        self.FromUser = users.GetSingleRecipient(self.FromEmail)
        self.RecipientList.append(self.FromUser)

        self.ToUsers = users.GetRecipients(self.ToEmailList)
        self.RecipientList += self.ToUsers

        if self.CCEmailList:
            self.CCUsers = users.GetRecipients(self.CCEmailList)
            self.RecipientList += self.CCUsers

    def ParseEmailAddresses(self):
        if self.From and '<' in self.From:
            self.FromEmail = self.From.split('<')[1].replace('>', '')

        if self.To:
            self.ToEmailList = ParseRecipientList(self.To)

        if self.CC:
            self.CCEmailList = ParseRecipientList(self.CC)

    def CreateMessageML(self):
        if self.Body_HTML_Raw and config.ParseHTML:
            # Translate HTML to MML
            pass
        elif self.Body_Text:
            # If there's no HTML in the email, revert to plain text
            self.Body_MML = CreateMMLFromText(self)
        elif self.Attachments:
            # If there's no body but there are attachments
            pass
        else:
            # The email has no interesting content, do not send to Symphony
            # and possibly send an error email back to the sender.
            self.IsValid = False

    def ParseEmailContent(self, msg: email_message):
        # ************ Try to create a unique identifier for each message ************
        if 'message-id' in msg:
            self.MessageId = msg['message-id']
            # print('Message-Id: ' + self.MessageId)

        self.PrimaryBoundary = msg.get_boundary(failobj='')
        # print('Primary Boundary: ' + self.PrimaryBoundary)

        simplest_content = msg.get_body(preferencelist=('plain', 'html'))
        richest_content = msg.get_body(preferencelist='html')

        if simplest_content and simplest_content.get_content_maintype() == 'text':
            if simplest_content.get_content_subtype() == 'plain':
                self.Body_Text = simplest_content.get_content()

        if richest_content and richest_content.get_content_maintype() == 'text':
            if richest_content.get_content_subtype() == 'html':
                # parse html message
                self.Body_HTML_Raw = richest_content.get_content()

        # _structure() gives me the mimetype heirarchy of the message
        # print(_structure(msg))
        # Parse attachments
        if config.ParseAttachments:
            for subpart in msg.walk():
                if subpart.get_content_disposition() == 'attachment':
                    att = ParseAttachment(subpart)

                    if att:
                        self.Attachments.append(att)


def ParseRecipientList(address_str: str):
    ret_list = []

    if address_str:
        addy_list = address_str.split(',')
        for rcpt in addy_list:
            addy = rcpt
            if '<' in rcpt:
                addy = rcpt.split('<')[1].replace('>', '')

            ret_list.append(addy.lower().strip())

    return ret_list


def ParseAttachment(email_attachment):
    try:
        name = email_attachment.get_filename()
        mime_type = email_attachment.get_content_type()

        if name:
            ext = os.path.splitext(email_attachment.get_filename())[1]
        else:
            ext = mimetypes.guess_extension(mime_type)
            name = str(uuid.uuid4()) + '.' + ext

        data = email_attachment.get_content()

        if data:
            return models.MessageAttachment(name, ext, data, mime_type)

        return None

    except Exception as ex:
        exc.LogException(ex, 'Unable to parse attachment.')


def CreateMMLFromText(parsed_email: EmailMessage):

    from_str = parsed_email.From.replace('<', '(').replace('>', ')')
    to_str = parsed_email.To.replace('<', '(').replace('>', ')')
    subject = parsed_email.Subject if parsed_email.Subject else '(blank)'
    body_str = parsed_email.Body_Text if parsed_email.Body_Text else '(blank)'

    if not parsed_email.FromUser.Is_Bounced:
        from_mention = '<mention uid="' + parsed_email.FromUser.Id + '"/>'
    else:
        from_mention = parsed_email.FromUser.Email

    to_mentions = []
    for rcp in parsed_email.ToUsers:
        if rcp.Is_Stream and rcp.Room_Name:
            to_mentions.append(rcp.Room_Name)
        elif not rcp.Is_Stream and not rcp.Is_Bounced:
            to_mentions.append('<mention uid="' + rcp.Id + '"/>')
        else:
            to_mentions.append(rcp.Email)

    body = "<messageML>E-mail received from: " + from_mention + "<br/><br/>"
    body += '<b class="tempo-text-color--secondary">To</b>: ' + ', '.join(to_mentions) + "<br/><br/>"

    if parsed_email.CCUsers:
        cc_mentions = []
        for rcp in parsed_email.CCUsers:
            if rcp.Is_Stream and rcp.Room_Name:
                cc_mentions.append(rcp.Room_Name)
            elif not rcp.Is_Stream and not rcp.Is_Bounced:
                cc_mentions.append('<mention uid="' + rcp.Id + '"/>')
            else:
                cc_mentions.append(rcp.Email)

        body += '<b class="tempo-text-color--theme-accent">CC</b>: ' + ', '.join(cc_mentions) + "<br/><br/>"

    body += '<b class="tempo-text-color--theme-accent">Subject</b>: ' + subject + "<br/><br/>"

    # Check that body_str is less than 2500 words
    msg_body = util.TruncateBodyText(body_str)
    body += '<b class="tempo-text-color--theme-accent">Message</b>: ' + "<br/>".join(msg_body.splitlines())
    body += "</messageML>"

    return body
