from collections import defaultdict
import re
from typing import Dict, List, Set, Tuple


def get_text_from_file(filename: str) -> str:
    """Returns the contents of text file."""
    with open(filename) as file:
        return file.read()


def get_text_snippets(filename: str, keywords: List[str]) -> Dict[str, Set[str]]:
    """
    Given a list of keywords to look for in a text file, this function uses
    RegEx matching to return all text snippets (delimited by periods) that
    contain the keywords.
    """
    # read the contents of file (this could take some time)
    text = get_text_from_file(filename)

    # find the keywords occurrences
    matches = match_keywords(text, keywords)

    # regular expression patterns
    # NOTE: \s+ matches one or more whitespace characters
    #       \. matches periods
    pattern_period = re.compile(r'\.\s+', flags=re.IGNORECASE)
    pattern_period_inverse = re.compile(r'\s+\.', flags=re.IGNORECASE)

    # find the whole snippets where the keywords were found
    snippets = defaultdict(set)
    for keyword, occurrences in matches.items():
        for occurrence in occurrences:

            # take the positions to look near the keyword
            start, end = occurrence

            # get the positions of start and end of the snippet
            snippet_start = len(text) - pattern_period_inverse.search(
                text[::-1], # inverted text
                len(text) - start - 1
            ).start()
            snippet_end = pattern_period.search(text, end).start() + 1

            # get snippet and add it to result
            snippet = text[snippet_start:snippet_end].replace('\n', '')
            snippets[keyword].add(snippet)

    # return snippets
    return snippets


def match_keywords(text: str, keywords: List[str]) -> Dict[str,
                                                           Set[Tuple[int, int]]]:
    """
    Given a list of keywords to look for in a text file, this function uses
    RegEx matching to return all keywords occurrences positions.
    """
    # regular expression patterns
    # NOTE: \b matches the empty string
    #       | is the OR operator
    pattern_keyword = re.compile(
        '|'.join([r'\b%s\b' % keyword for keyword in keywords]),
        flags=re.IGNORECASE
    )

    # find the keywords
    matches = defaultdict(set)
    pos = 0
    while True:

        # .search() always finds the first occurrence after the given position
        match = pattern_keyword.search(text, pos)

        # match found: add it and its position and update position
        if match:
            matches[match[0]].add(match.span())
            pos = match.end()
            continue

        # no match found: end of document
        break

    # return matches
    return matches
