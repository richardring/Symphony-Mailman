# from collections import Counter  # Used to count the _occurence_ of each word
import utility as util

def WordCount(input_text: str) -> int:
    if input_text:
        return len(input_text.split())

    return 0


# https://stackoverflow.com/a/1884277
def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


@util.benchmark
def CreateUniqueId(msg):
    hash_builder = [msg.FromUser.Email]
    hash_builder += [u.Email for u in msg.ToUsers]
    hash_builder += [u.Email for u in msg.CCUsers]
    # Remove whitespace from subject before appending
    hash_builder.append("".join(msg.Subject.split()))
    hash_builder.append(msg.PrimaryBoundary)

    uid = hash("".join(hash_builder))
    print('Unique-ish Id: ' + str(uid))

    return uid
