import json

import botlog as log
import symphony.connection as conn
import symphony.endpoints as ep
import symphony.utility as util


def SendEcho(message: str):
    endpoint = ep.Echo_Endpoint()
    payload = {
        "message": message
    }

    response = conn.SymphonyPOST(endpoint, payload)
    return LogMessagePost(response, 'echo', message)


def SendUserIMv2(userIds: list, message: str, data=None):
    return SendUserIM(userIds, message, endpoint_version=4, data=data)


def SendUserIM(userIds: list, message: str, endpoint_version: int=2, data=None):
    endpoint = ep.CreateIM_Endpoint()

    body = [int(uid) for uid in userIds]

    resp = conn.SymphonyPOST(endpoint, body)

    response = resp.json()

    streamId = response['id']

    if endpoint_version == 2:
        return SendSymphonyMessage(streamId, message)
    else:
        return SendSymphonyMessageV2(streamId, message, data)


def SendSymphonyMessage(stream_id: str, message: str):
    msg = util.FormatSymphonyMessage(message)
    endpoint = ep.SendMessage_Endpoint(stream_id)

    body = { "message": msg, "format": "MESSAGEML"}

    response = conn.SymphonyPOST(endpoint, body)
    return LogMessagePost(response, stream_id, message)


def SendSymphonyMessageV2(stream_id: str, message: str, data=None):
    msg = util.FormatSymphonyMessage(message)
    endpoint = ep.SendMessage_Endpoint(stream_id, 4)

    if data is not None:
        data = json.dumps(data)

    bodyObj = { "message": message, "data": data }
    response = conn.SymphonyPOSTv2(endpoint, bodyObj)
    return LogMessagePost(response, stream_id, message)


def LogMessagePost(response, stream_id: str, message: str=''):
    print('API Response: ' + response.text)
    if response.status_code == 200:
        resp = 'Sent Message | Stream Id: ' + stream_id + ' | Message: ' + message
    else:
        resp = 'Failed to send message | Stream Id: ' + stream_id + ' | Message: ' + message

    log.LogConsoleInfo(resp)
    return resp