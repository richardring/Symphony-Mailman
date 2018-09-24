import requests

import config

sym_session = requests.Session()
sym_session.cert = config.BotCertificate

sym_session_v2 = requests.Session()
sym_session_v2.cert = config.BotCertificate

Session_Token = None
KM_Token = None
Valid_Until = None
