from datetime import datetime, timedelta
import json
import requests

import botlog as log
import config
import exceptions
import symphony
import symphony.endpoints as ep


def GetAuthToken(endpoint):
    try:

        response = requests.post(endpoint, cert=config.OBOAppCertificate)

        if response.status_code == 200:
            resp_json = json.loads(response.text)
            return resp_json['token']

    except requests.exceptions.HTTPError as httpex:
        exceptions.LogWebException(httpex)

    except requests.exceptions.RequestException as connex:
        exceptions.LogRequestException(connex)

    except Exception as ex:
        exceptions.LogException(ex)

    return ''


def BuildOBOHeaders(sessionToken, contentType="application/json"):
    RESTheaders = {
        "sessionToken": sessionToken,
        "Content-Type": contentType,
        "User-Agent": "Postmaster (Kevin McGrath - BizOps - kevin.mcgrath@symphony.com)"
    }

    return RESTheaders


def AuthenticateOBO():
    log.LogConsoleInfoVerbose('Authenticating OBO App...')
    symphony.OBO_App_Token = GetAuthToken(ep.SessionAuth_OBO_App_Endpoint())

    log.LogConsoleInfoVerbose('OBO App Token: ' + symphony.OBO_App_Token)


def AuthenticateUserOBO(user_id: str):
    if not symphony.OBO_App_Token:
        AuthenticateOBO()

    endpoint = ep.SessionAuth_OBO_User_Endpoint(user_id)

    try:
        response = requests.post(endpoint, headers=BuildOBOHeaders(symphony.OBO_App_Token),
                                 cert=config.OBOAppCertificate)

        if response.status_code == 200:
            resp_json = json.loads(response.text)
            return resp_json['sessionToken']

    except requests.exceptions.HTTPError as httpex:
        exceptions.LogWebException(httpex)

    except requests.exceptions.RequestException as connex:
        exceptions.LogRequestException(connex)

    except Exception as ex:
        exceptions.LogException(ex)

    return ''
