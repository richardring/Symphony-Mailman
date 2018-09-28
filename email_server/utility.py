# from collections import Counter  # Used to count the _occurence_ of each word


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