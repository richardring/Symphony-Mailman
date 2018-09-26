import codecs
import json
import os
from pathlib import Path

config_prod_path = os.path.abspath("./config.json")
config_dev_path = os.path.abspath("./config_dev.json")

# Ensure I don't accidentally use my dev path on the server
dev_file = Path(config_dev_path)
config_path = config_dev_path if dev_file.is_file() else config_prod_path

with codecs.open(config_path, 'r', 'utf-8-sig') as config_json:
    _config = json.load(config_json)

# **************Symphony API Settings**************
BotUsername = _config['symphony']['bot_username']
SymphonyBaseURL = _config['symphony']['api_host'] + ':' + _config['symphony']['api_port']
SymphonyAuthBase = _config['symphony']['auth_host'] + ':' + _config['symphony']['auth_port']

SessionAuthURL = SymphonyAuthBase + '/sessionauth/v1/authenticate'
KMAuthURL = SymphonyAuthBase + '/keyauth/v1/authenticate'

_cert_folder = os.path.abspath('./' + _config['symphony']['cert_folder'])
_cert_file_path = os.path.join(_cert_folder, _config['symphony']['cert_filename'])
_key_file_path = os.path.join(_cert_folder, _config['symphony']['key_filename'])

BotCertificate = (_cert_file_path, _key_file_path)

UseRSA = _config['symphony']['use_rsa']
UseLegacyCrypto = _config['symphony']['use_legacy_crypto']
JWT_PublicKeyPath = os.path.join(_cert_folder, _config['symphony']['public_key_filename'])
JWT_PrivateKeyPath = os.path.join(_cert_folder, _config['symphony']['private_key_filename'])


# **************SMTP Server Settings**************
# The legacy implementation uses the smtpd library, now deprecated
# The modern implementation uses the aiosmtpd library: https://github.com/aio-libs/aiosmtpd
UseLegacySMTPServer = _config['smtp_server']['use_legacy']

BlockDuplicateMessages = _config['smtp_server']['block_duplicate_messages']

SMTPServerHost = _config['smtp_server']['host']
SMTPServerPort = _config['smtp_server']['port']
# Debugging Server settings only apply to legacy smtp server
UseDebuggingServer = _config['smtp_server']['debugging_server']
SMTPDebugHost = _config['smtp_server']['debug_host']
SMTPDebugPort = _config['smtp_server']['debug_port']

# Allow for saving local copies of inbound messages
SaveInboundEmail = _config['smtp_server']['save_inbound_email']
SaveInboundPath = _config['smtp_server']['save_inbound_path']

# Email security measures. Not necessary if using a relay
UseSPFChecking = _config['smtp_server']['use_spf']
UseDKIMChecking = _config['smtp_server']['use_dkim']
UseInboundWhitelist = _config['smtp_server']['use_inbound_whitelist']
Inbound_Whitelists = _config['inbound_whitelist']

# **************General Settings**************
ValidDomains = _config['valid_domains']
VerboseOutput = _config['verbose_output']
ParseHTML = _config['parse_html']
ParseAttachments = _config['parse_attachments']
LocalUsersOnly = _config['local_users_only']
StandardEmailDomain = _config['standard_email_domain']
UserEmailSeparator = _config['user_email_separator']

# **************Redis Settings**************
UseRedis = _config['redis']['use_redis']
RedisHost = _config['redis']['host']
RedisPort = _config['redis']['port']
RedisPassword = _config['redis']['password']

# **************SQLite Cache Settings**************
UseCache = _config['cache']['use_cache']
_cache_path = _config['cache']['cache_path']
_cache_filename = _config['cache']['cache_filename']
CachePath = os.path.abspath(os.path.join(_cache_path, _cache_filename))