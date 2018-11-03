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

        response = requests.post(endpoint, cert=config.BotCertificate)

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


def BuildHeaders(sessionToken, keyAuthToken, contentType="application/json"):
    RESTheaders = {
        "sessionToken": sessionToken,
        "keyManagerToken": keyAuthToken,
        "Content-Type": contentType,
        "User-Agent": "Postmaster (Kevin McGrath - BizOps - kevin.mcgrath@symphony.com)"
    }

    return RESTheaders


def Authenticate():
    log.LogConsoleInfoVerbose('Authenticating with Symphony...')
    symphony.Session_Token = GetAuthToken(ep.SessionAuth_Cert_Endpoint())

    log.LogConsoleInfoVerbose('Session Token: ' + symphony.Session_Token)

    symphony.KM_Token = GetAuthToken(ep.KMAuth_Cert_Endpoint())

    log.LogConsoleInfoVerbose('KM Token: ' + symphony.KM_Token)

    if symphony.KM_Token and symphony.KM_Token != '':
        symphony.Valid_Until = datetime.now() + timedelta(days=10)
        symphony.sym_session.headers.update(BuildHeaders(symphony.Session_Token, symphony.KM_Token))
        log.LogConsoleInfoVerbose('Authentication complete. Session valid until ' + symphony.Valid_Until.strftime('%c'))