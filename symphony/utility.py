import json


def FormatSymphonyMessage(message: str):
    if not message.startswith('<messageML>'):
        return "<messageML>" + message + "</messageML>"

    return message


def FormatSymphonyLink(url: str):
    return '<a href="' + url + '"/>'


def FormatSymphonyId(stream_id: str):
    return stream_id.replace('/', '_').replace('+', '-').replace('=', '').strip()


def FormatDicttoMML2(jsonObj: dict) -> str:
    json_str = json.dumps(jsonObj, indent=4, separators=(',', ': ')).replace('"', '&quot;').replace('\'', '&apos;')

    # apparently you need to include a newline character before the closing code tag. Why? ¯\_(-_-)_/¯
    json_str = "<code>" + json_str + "\n</code>"

    return json_str