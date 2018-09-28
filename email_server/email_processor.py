import botlog as log
import config
import symphony
import symphony.connection as conn
import symphony.messaging as messaging
import email_server.body_parser as parser
import email_server.exceptions as exc
import email_server.user_matching as users
from email_server.models import InboundMessage


# Processes the inbound email
# Step 1: Convert each recipient into a "real" email
# Step 2: Look up each "real" email to get a list of user_ids or stream_ids
# Step 3: Parse email body to be formatted into correct MessageML
# Step 4: Extract attachments
# Step 5: Create an MIM (if necessary) and send message with attachments
# Step 6: Send message to each room included, with attachments.
def ValidateUser(user_email: str):
    log.LogConsoleInfoVerbose('Attempting to validate user email address...')

    rcp = users.GetSingleRecipient(user_email)

    if rcp.Is_Bounced:
        # I don't want to reject the whole email if one recipient is not found
        # TODO: send 1-1 error report for sender
        log.LogSystemErrorVerbose('Unable to idenfity user or room with the email address: ' + user_email)
        return None
        # raise exc.SymphonyUserLookupException('Email address could not be identified as a valid user or room.')

    log.LogConsoleInfoVerbose('User identified: ' + rcp.Id + ' | Is Room: ' + str(rcp.Is_Stream))

    return rcp


def ProcessInboundEmail(message: InboundMessage):
    if config.UseRedis:
        log.LogConsoleInfoVerbose('Processing email asynchronously...')
        # Check to make sure the session is valid - it's possible the session and km token have
        # expired since the last time an email was processed.
        if not conn.IsValidSession():
            log.LogConsoleInfoVerbose('Session invalid, reauthenticating...')
            conn.Authenticate()

        ProcessAsync(message.mailfrom, message.rcpttos, message.data, symphony.Session_Token, symphony.KM_Token)
    else:
        log.LogConsoleInfoVerbose('Processing email synchronously...')
        Process(message.mailfrom, message.rcpttos, message.data)


# TODO: Implement the Redis async process
def ProcessAsync(sender: str, recipients: list, email_data, sym_session_token, sym_km_token):
    # Passing the tokens to the redis async process to avoid having to reauthenticate
    # each time a new email comes in.
    symphony.Session_Token = sym_session_token
    symphony.KM_Token = sym_km_token

    Process(sender, recipients, email_data)


def Process(sender: str, recipients: list, email_data):
    user_ids = []
    stream_ids = []

    # Validated the sender in handler_MAIL. If that passed, the sender
    # is now cached so the lookup is cheap. If it failed, the transaction
    # is cancelled anyway.
    # recipients.append(sender)

    log.LogConsoleInfoVerbose('Attempting to parse email message...')
    email = parser.ParseEmailMessage(email_data)

    log.LogConsoleInfoVerbose('Inbound Email Received: ' + 'From: ' + email.From +
                              ' || To: ' + email.To + ' || CC: ' + str(email.CC))

    # @@@@@@@@@@@@@@@ Attempt to identify the recipients @@@@@@@@@@@@@@@
    # I don't think I want to throw an exception if a user or room is not identified,
    # but I probably should send a bounce reply for the failed recipients.
    log.LogConsoleInfoVerbose('Attempting to parse recipients...')

    # I have to do this a different way. The envelope is modified when the
    # email is relayed, and I lose the information I was previously receiving
    # in handle_RCPT. Fortunately, the information is still part of the
    # email message, which I parse directly.
    rcp_list = email.RecipientList

    user_ids += [rcp.Id for rcp in rcp_list if not rcp.Is_Bounced and not rcp.Is_Stream]
    stream_ids += [rcp.Id for rcp in rcp_list if not rcp.Is_Bounced and rcp.Is_Stream]

    log.LogConsoleInfoVerbose('Done. Users found: ' + str(len(user_ids)) + ' Streams found: ' + str(len(stream_ids)))

    if email.IsValid:
        log.LogConsoleInfoVerbose('Done. Email subject: ' + email.Subject)

        # Send message to each stream
        if stream_ids:
            log.LogConsoleInfoVerbose('Attempting to forward email to stream list...')
            for stream_id in stream_ids:
                messaging.SendSymphonyMessageV2(stream_id, email.Body_MML, data=None, attachments=email.Attachments)

        # Only attempt to send an IM if there's more than one user, including the sender.
        if user_ids and len(user_ids) > 1:
            log.LogConsoleInfoVerbose('Attempting to forward email to MIM...')
            messaging.SendUserIMv2(user_ids, email.Body_MML, data=None, attachments=email.Attachments)

    else:
        # Alternatively, I can try to send an IM to the recipient telling them that there was a problem. Maybe
        # that's a better solution. At least if I can identify the sender. Though, if I can't identify
        # the sender, I should probably reject the whole shebang.
        log.LogConsoleInfoVerbose('Done. Email was marked invalid.')
        raise exc.SymphonyEmailBodyParseFailedException('Email could not be parsed.')


