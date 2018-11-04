import json
from typing import List

import botlog as log
import symphony.connection as conn
import symphony.connection_obo as conn_obo
import symphony.endpoints as ep
import symphony.utility as util
from email_server.models import MessageAttachment


def SendEcho(message: str):
    endpoint = ep.Echo_Endpoint()
    return conn.SymphonyPOST(endpoint, {"message": message})


def SendUserIMv2(userIds: list, message: str, data=None, attachments: List[MessageAttachment]=None, obo_user_id=None):
    return SendUserIM(userIds, message, endpoint_version=4, data=data, attachments=attachments, obo_user_id=obo_user_id)


def SendUserIM(userIds: list, message: str, endpoint_version: int=2, data=None,
               attachments: List[MessageAttachment]=None, obo_user_id: str=None):
    endpoint = ep.CreateIM_Endpoint()

    body = [int(uid) for uid in userIds]

    log.LogConsoleInfoVerbose('Attempting to create MIM...')

    # if obo_user_id:
        # resp = conn_obo.SymphonyPOST(endpoint, body, obo_user_id)
    # else:
    resp = conn.SymphonyPOST(endpoint, body)

    response = resp.json()

    streamId = response['id']
    log.LogConsoleInfoVerbose('MIM Stream Id: ' + streamId)

    if endpoint_version == 2:
        return SendSymphonyMessage(streamId, message, obo_user_id=obo_user_id)
    else:
        log.LogConsoleInfoVerbose('Using v4 Message endpoint...')
        return SendSymphonyMessageV2(streamId, message, data, attachments, obo_user_id=obo_user_id)


def SendSymphonyMessage(stream_id: str, message: str, obo_user_id: str=None):
    msg = util.FormatSymphonyMessage(message)
    endpoint = ep.SendMessage_Endpoint(stream_id)

    body = {"message": msg, "format": "MESSAGEML"}

    if obo_user_id:
        response = conn_obo.SymphonyPOST(endpoint, body, obo_user_id)
    else:
        response = conn.SymphonyPOST(endpoint, body)

    LogMessagePost(response, stream_id, message)

    return response


def SendSymphonyMessageV2(stream_id: str, message: str, data=None, attachments: List[MessageAttachment]=None,
                          obo_user_id: str=None):
    msg = util.FormatSymphonyMessage(message)
    endpoint = ep.SendMessage_Endpoint(stream_id, 4)

    # To send multiple attachments with the same key, we need to use a slighly different
    # submission format for requests-toolbelt. Instead, the "fields" parameter
    # that gets passed to the MultipartEncoder should take a list of tuples
    # for all the parameters.
    # https://github.com/requests/toolbelt/issues/190#issuecomment-319900108
    body_list = [('message', msg)]

    if data is not None:
        data = json.dumps(data)
        body_list.append(('data', data))

    if attachments:
        for att in attachments:
            att_t = (att.Filename, att.Data, att.MIME)
            body_list.append(('attachment', att_t))

    if obo_user_id:
        response = conn_obo.SymphonyPOSTv2(endpoint, body_list, obo_user_id)
    else:
        response = conn.SymphonyPOSTv2(endpoint, body_list)

    LogMessagePost(response, stream_id, message)

    return response


def LogMessagePost(response, stream_id: str, message: str=''):
    if response.status_code == 200:
        resp = 'Sent Message | Stream Id: ' + stream_id
    else:
        resp = 'Failed to send message | Stream Id: ' + stream_id

    log.LogConsoleInfo(resp)