import re

import botlog as log
import config
import symphony.connection as conn
import symphony.connection_obo as conn_obo
import symphony.endpoints as ep


def RemoveNonAlpha(input_str: str):
    pattern = re.compile('[\W_]+')
    return re.sub(pattern, ' ', input_str.lower().strip())


def SearchRoomByName(room_name: str, obo_user_id: str=None):
    endpoint = ep.SearchRoom_Endpoint()

    query = room_name.replace('_', ' ').replace('.', ' ').replace('-', ' ').replace('+', ' ').strip().lower()
    query = re.sub(' +', ' ', query)

    body = {"query": query, "active": True, "private": True}

    if obo_user_id:
        resp = conn_obo.SymphonyPOST(endpoint, body, obo_user_id)
    else:
        resp = conn.SymphonyPOST(endpoint, body)

    response = resp.json()

    if response and response['rooms']:
        # log.LogConsoleInfoVerbose('The following rooms were found:')
        rooms = response['rooms']
        stream_id = None
        room_name = None

        if config.VerboseOutput:
            index = 1
            for room in rooms:
                sid = room['roomSystemInfo']['id']
                name = room['roomAttributes']['name']

                # log.LogConsoleInfoVerbose('Room ' + str(index) + ': ' + name + ' (' + sid + ')')
                index += 1

        for room in rooms:
            sid = room['roomSystemInfo']['id']
            name = room['roomAttributes']['name']
            # If one of the rooms has an exact match (when changed to lowercase)
            # use that room.
            # TODO: Decide how to select a room if the match isn't perfect
            # log.LogConsoleInfoVerbose('Trying Match - query: ' + query + ' room name: ' + name)
            # log.LogConsoleInfoVerbose('Stream Id: ' + str(stream_id))
            # log.LogConsoleInfoVerbose('Is match? ' + str(name.lower() == query))

            if not stream_id and RemoveNonAlpha(name) == query:
                stream_id = sid
                room_name = name
                log.LogConsoleInfoVerbose('Selecting ' + name + ' as matched Room. (' + stream_id + ')')

                break

        return stream_id, room_name

    return None, None
