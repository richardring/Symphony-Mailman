# https://docs.python.org/3/library/email.examples.html
from email import message as email_message
from email import policy
from email.iterators import typed_subpart_iterator as iter_sub
from email.iterators import _structure
from email.parser import BytesParser
import mimetypes
import os
import uuid

import config
import email_server.models as models
import exceptions as exc


def ParseEmailMessage(email_data):
    # BytesParser(policy) is required to expose the .get_body() method.
    return EmailMessage(BytesParser(policy=policy.default).parsebytes(email_data))


class EmailMessage:
    def __init__(self, parsed_message: email_message):
        self.From = parsed_message['from']
        # Might need to figure out how to break these users into objects so I can sep
        # the name from the email
        self.To = parsed_message['to']
        self.Subject = parsed_message['subject']
        self.Body_Text = None
        self.Body_HTML_Raw = None
        self.Body_MML = None
        self.Attachments = []
        self.IsValid = True

        self.ParseEmailContent(parsed_message)
        self.CreateMessageML()

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


def CreateMMLFromText(parsed_email):

    from_str = parsed_email.From.replace('<', '(').replace('>', ')')
    to_str = parsed_email.To.replace('<', '(').replace('>', ')')
    subject = parsed_email.Subject if parsed_email.Subject else '(blank)'
    body_str = parsed_email.Body_Text if parsed_email.Body_Text else '(blank)'

    body = "<messageML>Forwarded e-mail message from: " + from_str + "<br/>"
    body += "<b>To</b>: " + to_str + "<br/>"
    body += "<b>Subject</b>: " + subject + "<br/>"
    body += "<b>Body</b>: " + "<br/>".join(body_str.splitlines())
    body += "</messageML>"


    return body





