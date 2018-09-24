from IPy import IP

import config

_whitelist_set = []

# See: http://www.topdog.za.net/2012/05/06/python-modules-you-should-know%3a-ipy/
# https://github.com/autocracy/python-ipy
def IsWhitelistedIP(ip_address: str):
    global _whitelist_set
    # Build the white list
    # TODO: This probably needs to be optimized

    if not _whitelist_set:
        for whitelist in config.Inbound_Whitelists:
            _whitelist_set.append(IP(whitelist))

    return any([ip_address in whitelist_item for whitelist_item in _whitelist_set])


