from requests.exceptions import HTTPError
import urllib.parse as u_enc

import botlog as log
import exceptions as exc
import symphony.connection as conn
import symphony.endpoints as ep


def LookupUser(user_email: str):
    log.LogConsoleInfoVerbose('Attempting lookup for: ' + user_email)

    endpoint = ep.LookupUser_Endpoint(u_enc.quote_plus(user_email))
    resp = conn.SymphonyGET(endpoint)

    # Apparently, if you do a lookup and the system finds no results, instead of
    # sending a 200 with an empty array or throwing an error, it sends
    # a 204. What's the point of having an error object included
    # in the specification if you're just going to return a 204?
    # The point is the platform are a bunch of monkeys.
    if resp.status_code == 200:
        response = resp.json()

        log.LogConsoleInfoVerbose('User Lookup Response: ' + str(response))

        if response:
            users = response['users']
            errors = response['errors']

            if users:
                id = str(users[0]['id'])
                log.LogConsoleInfoVerbose('User Id: ' + id)
                return id
            elif errors:
                err = errors[0]['error']
                log.LogSystemError('Unable to match email: ' + user_email + ' Error: ' + err)

    return None


def LookupUsersByEmail(user_emails: list):
    user_ids = set()
    errors = []

    # In the rare case that there are more than 50 user emails to lookup,
    # break the list of emails into smaller groups. The API specifies it
    # can handle groups of 100, but I don't trust it, so I do 50.
    email_buckets = [user_emails[index:index + 50] for index in range(0, len(user_emails), 50)]

    for user_list in email_buckets:
        endpoint = ep.LookupUserList_Endpoint(user_list)

        try:
            response = conn.SymphonyGET(endpoint).json()

            users = response['users']
            errors += response['errors']

            # Using the union operator to concat each group of users into
            # the resultant set (thus ensuring each userId only appears once
            user_ids |= set([str(u['id']) for u in users])

        # The API throws an HTTP400 when no results are found. Which... I have opinions on.
        except HTTPError as httpex:
            exc.LogWebException(httpex, 'Error during user lookup.')

    if errors and len(errors) > 0:
        log.LogSystemError('Unable to match some emails')
        log.LogSystemError(str(errors))

    return list(user_ids) if len(user_ids) > 0 else None


def SearchUsers(name_query: str):
    log.LogConsoleInfoVerbose('Searching for user: ' + name_query)
    endpoint = ep.SearchUser_Endpoint()
    query = name_query.replace('_', ' ').replace('.', ' ').replace('-', ' ').replace('+', ' ')

    body = {"query": query}
    resp = conn.SymphonyPOST(endpoint, body)

    if resp.status_code == 200:
        response = resp.json()

        if response and response['count'] and response['count'] > 0:
            id = str(response['users'][0]['id'])
            log.LogConsoleInfoVerbose('User found. Id: ' + id)
            return id

    return None


def SearchUsersFull(first_name: str = None, last_name: str = None, display_name: str = None):
    query_list = []

    if first_name is not None:
        query_list.append(first_name.strip())

    if last_name is not None:
        query_list.append(last_name.strip())

    if display_name is not None:
        query_list.append(display_name.strip())

    query = ' '.join(query_list)

    if query and not query.isspace():
        endpoint = ep.SearchUser_Endpoint()
        body = {"query": query}

        response = conn.SymphonyPOST(endpoint, body).json()

        if response and response['count'] and response['count'] > 0:
            return str(response['users'][0]['id'])

    return None
