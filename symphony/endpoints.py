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


def SessionAuth_OBO_App_Endpoint():
    return config.OBOAuthBase + '/sessionauth/v1/app/authenticate'


def SessionAuth_OBO_User_Endpoint(user_id: str):
    return config.OBOAuthBase + '/sessionauth/v1/app/user/' + user_id + '/authenticate'


def Echo_Endpoint():
    return config.SymphonyBaseURL + '/agent/v1/util/echo'


def CreateIM_Endpoint(exclude_bot: bool = False):
    imEP = config.SymphonyBaseURL + '/pod/v1/'
    imEP += 'admin/' if exclude_bot else ''
    imEP += 'im/create'

    return imEP


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


def ListUserStreams_Endpoint(limit: int=50, skip: int=0):
    return config.SymphonyBaseURL + '/pod/v1/streams/list?limit=' + str(limit) + '&skip=' + str(skip)


def SetPresence_Endpoint():
    return config.SymphonyBaseURL + '/pod/v2/user/presence'
