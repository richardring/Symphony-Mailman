# from collections import Counter  # Used to count the _occurence_ of each word
import utility as util


def TruncateBodyText(input_text: str) -> str:
    output_text = input_text

    if input_text:
        # The api limits by words, not characters? Why? Who the hell knows why.
        # Regardless, the break is on whitespace. I'm only going to include
        # actual spaces, and reduce the count to 2000 instead of 2500
        if input_text.count(' ') > 2000:
            output_text = ' '.join(input_text.split(' ')[:2000])
            output_text += '<br/><br/><b>NOTE</b>: Message was truncated to comply with API limits. '
            output_text += 'Please keep messages under 2000 words.'

    return output_text


# https://stackoverflow.com/a/1884277
def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


def CreateUniqueId(msg):
    hash_builder = [msg.FromUser.Email]
    hash_builder += [u.Email for u in msg.ToUsers]
    hash_builder += [u.Email for u in msg.CCUsers]
    # Remove whitespace from subject before appending
    hash_builder.append("".join(msg.Subject.split()))
    #hash_builder.append(msg.PrimaryBoundary)

    pre_hash = "".join(hash_builder)
    #print(pre_hash)
    uid = hash(pre_hash)
    # print('Unique-ish Id: ' + str(uid))

    return uid
