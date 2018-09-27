import botlog as log
import config
from email_server import User_Cache
import exceptions
import symphony.user as users
import symphony.chatroom as room

# 7696581394433 uid is 13 chars on corp. May not be true in general

# Email Formats:
# kevin.mcgrath@podname.symphony.com => kevin.mcgrath@symphony.com
# kevin_mcgrath@podname.symphony.com => "
# 111222333444@podname.symphony.com => " (assumes the number is a user id, bypasses lookup)
#
# For the long form case, each subdomain.domain.com must be defined in config.json
# kevin.mcgrath.subdomain.domain.com@podname.symphony.com => kevin.mcgrath@subdomain.domain.com
# kevin.mcgrath*subdomain.domain.com@podname.symphony.com => kevin.mcgrath@subdomain.domain.com
#
# For Rooms/Streams
# my.room.name@podname.symphony.com
# my_room_name@podname.symphony.com
# my+room+name@podname.symphony.com
# searches for the stream id for "My Room Name"
# myk_SV7fmn3_5s1f1UhQeX___qLndD0UdA@podname.symphony.com will bypass the room search and assume a the local part is
# a stream id iff the parser detects the presence of three consecutive underscore characters.

# Parsing Order:
# Recipient email addresses will be run through the identification system until a successful user_id or stream_id
# is obtained from the symphony API. The checks will proceed in this order:
# 0. Check cache for pre-discovered email addresses
# 1. Check if local part is numeric => assume user_id
# 2. Check if local part contains "___" (three underscores) => assume stream_id
# 3. Check if local part contains any domains listed in settings.valid_domains => Lookup email with @ between
#       matched domain and remainder of the local part
# 4. Lookup for email of form:  local_part@standard_email_domain
# 5. Search for room, replacing all special chars with spaces
# 6. Search for users, replacing all special chars with spaces

# Process Results
# 1. If all recipients are identified, send message, do not reply
# 2. If one or more recipients are not identified or are unrecoverably ambiguous, send email to
#       sender with list of unidentifiable email addresses


def GetRecipient(user_email):
    return IdentifyParticipant(user_email)


def GetRecipients(recipient_list):
    rcp_list = []

    for email_address in recipient_list:
        rcp_list.append(IdentifyParticipant(email_address))

    return rcp_list


# Using short-circuiting here to evaluate each step in turn and return the first
# valid recipient record found
def IdentifyParticipant(r_email: str):
    rcp = CheckCache(r_email)

    if not rcp:
        rcp = CheckIsUserId(r_email) or CheckIsStreamId(r_email) or CheckIsFullEmail(r_email)\
            or CheckIsStandardEmail(r_email) or CheckIsRoomName(r_email)\
            or SearchUser(r_email) or SearchUser(r_email, local_part_only=True)

        if not rcp:
            # If the email address is not found, create a default recipient to be used
            # for a bounce reply
            rcp = Recipient(r_email)

        # Add value to the cache for future use. Including failed lookups.
        User_Cache.Insert_Id(r_email, rcp.Id, 'preview')

    return rcp


def SearchUser(r_email: str, local_part_only: bool=False):
    log.LogConsoleInfoVerbose('S6 - Searching users for ' + r_email)
    search_param = r_email.split('@')[0] if local_part_only else r_email

    id = users.SearchUsers(search_param)

    if id:
        return Recipient(r_email, id, False)

    return None


# Step 5
def CheckIsRoomName(r_email: str):
    log.LogConsoleInfoVerbose('S5 - Checking if ' + r_email + ' is a room name.')
    local_part = r_email.split('@')[0]

    stream_id = room.SearchRoomByName(local_part)

    if stream_id:
        return Recipient(r_email, stream_id, True)

    return None


# Step 4
def CheckIsStandardEmail(r_email: str):
    log.LogConsoleInfoVerbose('S4.1 - User Lookup (standard) on ' + r_email)
    local_part = r_email.split('@')[0]

    if config.StandardEmailDomain:
        new_email = local_part + '@' + config.StandardEmailDomain
        log.LogConsoleInfoVerbose('S4.2 - Lookup (standard) for resolved email:  ' + new_email)

        id = users.LookupUser(new_email)

        if id:
            return Recipient(r_email, id, False)

    return None


# Step 3
def CheckIsFullEmail(r_email: str):
    log.LogConsoleInfoVerbose('S3.1 - User Lookup on ' + r_email)
    new_email = None
    local_part = r_email.split('@')[0]
    domain_list = config.ValidDomains

    for domain in domain_list:
        if domain in local_part:
            idx = local_part.index(domain)
            new_local = local_part[:idx - 1]

            new_email = new_local + '@' + domain
            break

    if new_email:
        log.LogConsoleInfoVerbose('S3.2 - Lookup for resolved email: ' + new_email)
        id = users.LookupUser(new_email)

        if id:
            return Recipient(r_email, id, False)

    return None


# Step 2
def CheckIsStreamId(r_email: str):
    log.LogConsoleInfoVerbose('S2 - Checking if ' + r_email + ' contains a stream id.')
    local_part = r_email.split('@')[0]

    if "___" in local_part:
        return Recipient(r_email, local_part, True)

    return None


# Step 1
def CheckIsUserId(r_email: str):
    log.LogConsoleInfoVerbose('S1 - Checking if ' + r_email + ' contains a user id.')
    local_part = r_email.split('@')[0]

    if local_part.isnumeric():
        return Recipient(r_email, local_part, False)

    return None


# Step 0
def CheckCache(r_email: str):
    if config.UseCache:
        log.LogConsoleInfoVerbose('S0 - Checking Cache for ' + r_email)
        try:
            id = User_Cache.Get_Id(r_email)

            if id:
                if id.isnumeric():
                    return Recipient(r_email, id, False)
                elif "___" in id:
                    return Recipient(r_email, id, True)
        except Exception as ex:
            exceptions.LogException(ex)

    return None


class Recipient:
    def __init__(self, email, id="-1", is_stream=False):
        self.Email = email
        self.Id = id
        self.Is_Stream = is_stream
        self.Is_Bounced = self.Id == "-1"
