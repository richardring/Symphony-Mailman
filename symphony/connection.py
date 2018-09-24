from datetime import datetime, timedelta
import json
import requests
from requests_toolbelt import MultipartEncoder

import botlog as log
import config
import exceptions
import symphony
import symphony.auth_cert as auth_cert
import symphony.auth_jwt as auth_jwt


def IsValidSession():
    return symphony.Session_Token and datetime.now() < symphony.Valid_Until


def Authenticate():
    if config.UseRSA:
        auth_jwt.Authenticate()
    else:
        auth_cert.Authenticate()


# This may not be necessary, I'm not sure if the headers will change for RSA
def BuildHeaders(sessionToken: str, keyAuthToken: str, contentType: str="application/json"):
    if config.UseRSA:
        return auth_jwt.BuildHeaders(sessionToken, keyAuthToken, contentType)
    else:
        return auth_cert.BuildHeaders(sessionToken, keyAuthToken, contentType)


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


def SymphonyPOST(endpoint: str, body):
    return SymphonyREST('POST', endpoint, json.dumps(body))


def SymphonyPOSTv2(endpoint: str, body):
    return SymphonyREST('POSTv2', endpoint, body)


def SymphonyGET(endpoint):
    return SymphonyREST('GET', endpoint, None)


def SymphonyREST(method, endpoint, body):
    response = None

    if not IsValidSession():
        Authenticate()

    try:
        if method == 'GET':
            response = symphony.sym_session.get(endpoint)
        elif method == 'POST':
            response = symphony.sym_session.post(endpoint, data=body)
        elif method == 'POSTv2':
            encoder = MultipartEncoder(fields=body)
            headers = BuildHeaders(symphony.Session_Token, symphony.KM_Token, encoder.content_type)

            symphony.sym_session_v2.headers.update(headers)

            response = symphony.sym_session_v2.post(endpoint, data=encoder)
        else:
            raise MethodNotImplementedException(method + ' is not yet implemented.')

        if response.status_code // 100 != 2:
            response.raise_for_status()

    except requests.exceptions.HTTPError as httpex:
        exceptions.LogWebException(httpex, response.text)

    except requests.exceptions.RequestException as connex:
        exceptions.LogRequestException(connex)

    except Exception as ex:
        exceptions.LogException(ex)
    finally:
        return response


class MethodNotImplementedException(Exception):
    pass