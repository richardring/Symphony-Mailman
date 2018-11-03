import json
import requests
from requests_toolbelt import MultipartEncoder

import config
import exceptions
import symphony
import symphony.auth_obo as obo


# This may not be necessary, I'm not sure if the headers will change for RSA
def BuildUserHeaders(userSessionToken: str, contentType: str="application/json"):
    RESTheaders = {
        "sessionToken": userSessionToken,
        "Content-Type": contentType,
        "User-Agent": "Postmaster (Kevin McGrath - BizOps - kevin.mcgrath@symphony.com)"
    }

    return RESTheaders


def SymphonyPOST_OBO(endpoint: str, body, user_id: str):
    return SymphonyREST('POST', endpoint, json.dumps(body), user_id)


def SymphonyPOSTv2(endpoint: str, body, user_id: str):
    return SymphonyREST('POSTv2', endpoint, body, user_id)


def SymphonyGET(endpoint: str, user_id: str):
    return SymphonyREST('GET', endpoint, None, user_id)


def SymphonyREST(method: str, endpoint: str, body, user_id: str):
    response = None

    try:
        user_session_token = obo.AuthenticateUserOBO(user_id)
        obo_user_headers = BuildUserHeaders(user_session_token)


        if method == 'GET':
            response = requests.get(endpoint, headers=obo_user_headers)
        elif method == 'POST':
            response = requests.post(endpoint, data=body, headers=obo_user_headers)
        elif method == 'POSTv2':
            encoder = MultipartEncoder(fields=body)
            obo_user_headers = BuildUserHeaders(user_session_token, encoder.content_type)

            # symphony.sym_session_v2.headers.update(headers)

            response = requests.post(endpoint, data=encoder, headers=obo_user_headers)
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