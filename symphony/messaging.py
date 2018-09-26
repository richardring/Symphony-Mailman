import json
from typing import List

import botlog as log
import symphony.connection as conn
import symphony.endpoints as ep
import symphony.utility as util
from email_server.models import MessageAttachment


def SendEcho(message: str):
    endpoint = ep.Echo_Endpoint()
    payload = {
        "message": message
    }

    response = conn.SymphonyPOST(endpoint, payload)
    return LogMessagePost(response, 'echo', message)


def SendUserIMv2(userIds: list, message: str, data=None, attachments: List[MessageAttachment]=None):
    return SendUserIM(userIds, message, endpoint_version=4, data=data, attachments=attachments)


def SendUserIM(userIds: list, message: str, endpoint_version: int=2, data=None,
               attachments: List[MessageAttachment]=None):
    endpoint = ep.CreateIM_Endpoint()

    body = [int(uid) for uid in userIds]

    resp = conn.SymphonyPOST(endpoint, body)

    response = resp.json()

    streamId = response['id']

    if endpoint_version == 2:
        return SendSymphonyMessage(streamId, message)
    else:
        return SendSymphonyMessageV2(streamId, message, data, attachments)


def SendSymphonyMessage(stream_id: str, message: str):
    msg = util.FormatSymphonyMessage(message)
    endpoint = ep.SendMessage_Endpoint(stream_id)

    body = { "message": msg, "format": "MESSAGEML"}

    response = conn.SymphonyPOST(endpoint, body)

    LogMessagePost(response, stream_id, message)

    return response


def SendSymphonyMessageV2(stream_id: str, message: str, data=None, attachments: List[MessageAttachment]=None):
    msg = util.FormatSymphonyMessage(message)
    endpoint = ep.SendMessage_Endpoint(stream_id, 4)

    bodyObj = { "message": msg }

    if data is not None:
        data = json.dumps(data)
        bodyObj['data'] = data

    if attachments:
        att_list = []
        for att in attachments:
            att_t = (att.Filename, att.Data, att.MIME)
            att_list.append(att_t)

        bodyObj['attachment'] = att_list

    response = conn.SymphonyPOSTv2(endpoint, bodyObj)

    LogMessagePost(response, stream_id, message)

    return response


def LogMessagePost(response, stream_id: str, message: str=''):
    print('API Response: ' + response.text)
    if response.status_code == 200:
        resp = 'Sent Message | Stream Id: ' + stream_id + ' | Message: ' + message
    else:
        resp = 'Failed to send message | Stream Id: ' + stream_id + ' | Message: ' + message

    log.LogConsoleInfo(resp)