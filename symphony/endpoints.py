import config
import symphony.utility as util


def SessionAuth_Cert_Endpoint():
    return config.SymphonyAuthBase + '/sessionauth/v1/authenticate'


def KMAuth_Cert_Endpoint():
    return config.SymphonyAuthBase + '/keyauth/v1/authenticate'


def SessionAuth_JWT_Endpoint():
    return config.SymphonyAuthBase + '/login/pubkey/authenticate'


def KMAuth_JWT_Endpoint():
    return config.SymphonyAuthBase + '/relay/pubkey/authenticate'


def Echo_Endpoint():
    return config.SymphonyBaseURL + '/agent/v1/util/echo'


def CreateIM_Endpoint():
    return config.SymphonyBaseURL + '/pod/v1/im/create'


def SendMessage_Endpoint(stream_id: str, version: int=2):
    s_id = util.FormatSymphonyId(stream_id)
    return config.SymphonyBaseURL + '/agent/v' + str(version) + '/stream/' + s_id + '/message/create'


def LookupUserList_Endpoint(user_emails: list):
    qs = ','.join(user_emails)
    return config.SymphonyBaseURL + '/pod/v3/users?local=' + str(config.LocalUsersOnly).lower() + '&email=' + qs


def LookupUser_Endpoint(user_email: str):
    return config.SymphonyBaseURL + '/pod/v3/users?local=' + str(config.LocalUsersOnly).lower() + '&email=' + user_email


def SearchUser_Endpoint():
    return config.SymphonyBaseURL + '/pod/v1/user/search?local=' + str(config.LocalUsersOnly).lower()


def FindUser_Endpoint():
    return config.SymphonyBaseURL + '/pod/v1/admin/user/find'


def SearchRoom_Endpoint():
    return config.SymphonyBaseURL + '/pod/v3/room/search?limit=5'
