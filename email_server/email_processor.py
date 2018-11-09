import botlog as log
import config
import symphony
import symphony.connection as conn
import symphony.messaging as messaging
import email_server.body_parser as parser
import email_server.exceptions as exc
import email_server.integrity as dupe_c
import email_server.user_matching as users
from email_server.models import InboundMessage


# Processes the inbound email
# Step 1: Convert each recipient into a "real" email
# Step 2: Look up each "real" email to get a list of user_ids or stream_ids
# Step 3: Parse email body to be formatted into correct MessageML
# Step 4: Extract attachments
# Step 5: Create an MIM (if necessary) and send message with attachments
# Step 6: Send message to each room included, with attachments.
def VerifySymphonyConnection():
    response = messaging.SendEcho('Test Message')
    return response.status_code == 200


def ValidateSender(sender_email: str):
    log.LogConsoleInfoVerbose('Attempting to validate sender email address...')

    return users.IdentifySender(sender_email)


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
# TODO: Refactor async a bit so just the symphony components are async (keep the dupe checking intact)
def ProcessAsync(sender: str, recipients: list, email_data, sym_session_token, sym_km_token):
    # Passing the tokens to the redis async process to avoid having to reauthenticate
    # each time a new email comes in.
    symphony.Session_Token = sym_session_token
    symphony.KM_Token = sym_km_token

    Process(sender, recipients, email_data)


def Process(sender: str, recipients: list, email_data):
    log.LogConsoleInfoVerbose('Attempting to parse email message...')
    email = parser.ParseEmailMessage(email_data)

    # The parser uses the properties of each email (From:, To:, Subject, content-boundary)
    # to create a hash for comparison. Once submitted to Symphony, the hash is added to
    # a dupe_check dictionary for 2 mins. If a duplicate hash is found, the message is not sent.
    if dupe_c.IsDuplicateMessage(email):
        log.LogSystemInfoVerbose('Duplicate Messsage suppressed (' + str(email.Id) + ')')
        return

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

    # Convert the list comprehension to a set first to ensure we don't have any duplicate user/stream ids
    user_ids = list(set([rcp.Id for rcp in rcp_list if not rcp.Is_Bounced and not rcp.Is_Stream]))
    stream_ids = list(set([rcp.Id for rcp in rcp_list if not rcp.Is_Bounced and rcp.Is_Stream]))

    log.LogConsoleInfoVerbose('Done. Users found: ' + str(len(user_ids)) + ' Streams found: ' + str(len(stream_ids)))
    log.LogSystemInfoVerbose('User Ids: ' + str(user_ids))
    log.LogSystemInfoVerbose('Stream Ids: ' + str(stream_ids))

    if email.IsValid:
        log.LogConsoleInfoVerbose('Done. Email subject: ' + email.Subject)

        if stream_ids:
            log.LogConsoleInfoVerbose('Attempting to forward email to stream list...')
            for stream_id in stream_ids:
                if config.UseOnBehalfOf:
                    messaging.SendSymphonyMessageV2(stream_id, email.Body_MML, data=None, attachments=email.Attachments,
                                                    obo_user_id=email.FromUser.Id)
                else:
                    messaging.SendSymphonyMessageV2(stream_id, email.Body_MML, data=None, attachments=email.Attachments)

        if user_ids:
            log.LogConsoleInfoVerbose('Attempting to forward email to IM/MIM...')

            if len(user_ids) > 1 and config.UseOnBehalfOf:
                messaging.SendUserIMv2(user_ids, email.Body_MML, data=None, attachments=email.Attachments,
                                       obo_user_id=email.FromUser.Id)
            elif stream_ids and len(user_ids) == 1:
                # Do not send a Postmaster 1:1 if the only recipients are rooms and the sender.
                pass
            else:
                # If OBO is disabled or there is only one user (the sender), then create an IM/MIM with Postmaster
                messaging.SendUserIMv2(user_ids, email.Body_MML, data=None, attachments=email.Attachments)

        # Ensure the message is added to the dupe system after submission to Symphony.
        # TODO: Re-throw exceptions from Sym API. If the messages don't make it, retry? Maybe
        dupe_c.AddSentMessage(email)

    elif email.FromUser and email.FromUser.Id:
        subj = email.Subject if email.Subject else 'Unknown subject'
        messaging.SendUserIM(email.FromUser.Id, 'Email could not be sent to Symphony. (Subject: ' + subj + ')')
        log.LogConsoleInfoVerbose('Email was marked invalid. IM sent to From User.')
    else:
        log.LogConsoleInfoVerbose('Email was marked invalid.')
        raise exc.SymphonyEmailBodyParseFailedException('Email could not be parsed.')


