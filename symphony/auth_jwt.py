from datetime import datetime, timedelta
import json
import jwt
import requests

import botlog as log
import config
import exceptions
import symphony
import symphony.endpoints as ep


# GAE does not allow installation of the cryptography module
# Thus, I need to provide a way to fall back to the legacy modules
# required by pyJWT
if config.UseLegacyCrypto:
    from jwt.contrib.algorithms.pycrypto import RSAAlgorithm
    jwt.unregister_algorithm('RS512')
    jwt.register_algorithm('RS512', RSAAlgorithm(RSAAlgorithm.SHA512))


def GetAuthToken(endpoint, jwt_token):
    try:

        # This needs to be a string, or requests will use the wrong content type
        response = requests.post(endpoint, data=json.dumps(jwt_token))

        print(response)

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


def GenerateJWTAuthToken():
    Header = {
        "typ": "JWT",
        "alg": "RS512"
    }

    # Make sure you're using datetime.utcnow() and not datetime.now()
    Payload = {
        "sub": config.BotUsername,
        "exp": datetime.utcnow() + timedelta(minutes=5)
    }

    private_key = ''
    public_key = ''

    try:
        log.LogSystemInfoVerbose('Private key path: ' + config.JWT_PrivateKeyPath)
        log.LogSystemInfoVerbose('Public key path: ' + config.JWT_PublicKeyPath)

        with open(config.JWT_PrivateKeyPath, 'r') as keyfile:
            private_key = keyfile.read()

        with open(config.JWT_PublicKeyPath, 'r') as keyfile:
            public_key = keyfile.read()

    except FileNotFoundError as f_ex:
        exceptions.LogException(f_ex)
    except Exception as ex:
        exceptions.LogException(ex)

    if private_key:
        encoded = jwt.encode(Payload, private_key, algorithm='RS512', headers=Header)
        # log.LogConsoleInfoVerbose('encoded key: ')
        # log.LogConsoleInfoVerbose(encoded)
        # log.LogConsoleInfoVerbose('Expires on (epoch): ' + str(Payload['exp']))
        log.LogConsoleInfoVerbose('Expires on: ' + datetime.fromtimestamp(Payload['exp']).strftime('%m-%d-%Y %H:%M'))

        # decoded = jwt.decode(encoded, public_key, algorithms='RS512')
        # log.LogConsoleInfoVerbose('decoded key: ')
        # log.LogConsoleInfoVerbose(decoded)

        return encoded
    else:
        return None


def Authenticate():
    log.LogConsoleInfoVerbose('Generating JWT signing token...')
    jwt_token = GenerateJWTAuthToken()

    jwt_payload = {
        "token": jwt_token.decode('utf-8')
    }

    log.LogConsoleInfoVerbose('Authenticating with Symphony...')
    symphony.Session_Token = GetAuthToken(ep.SessionAuth_JWT_Endpoint(), jwt_payload)

    log.LogConsoleInfoVerbose('Session Token: ' + symphony.Session_Token)

    symphony.KM_Token = GetAuthToken(ep.KMAuth_JWT_Endpoint(), jwt_payload)

    log.LogConsoleInfoVerbose('KM Token: ' + symphony.KM_Token)

    if symphony.KM_Token and symphony.KM_Token != '':
        symphony.Valid_Until = datetime.now() + timedelta(days=10)
        symphony.sym_session.headers.update(BuildHeaders(symphony.Session_Token, symphony.KM_Token))
        log.LogConsoleInfoVerbose('Authentication complete. Session valid until ' + symphony.Valid_Until.strftime('%c'))