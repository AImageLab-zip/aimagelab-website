"""Where a lab member stands in a publication's author list (issue #13).

IRIS gives each publication one ordered string, "Rossi, Mario; Bianchi,
Anna", and no per-author position. The link table knows *which* lab member
a publication belongs to, because the importer fetches publications per
person (by codice fiscale). So the question is never "who are these
authors" - which homonyms would make unanswerable - but only "which of
these names is the person we already know", inside one paper.

`find_position()` answers it and says how sure it is. Counters built on it
must show the unresolved cases next to the numbers.

Equal contribution is not recorded by IRIS: "first" and "last" here mean
first-listed and last-listed.
"""
import re
import unicodedata

from .citations import split_authors

# The importer stores at most this many characters of the author string
# (tasks.py). A string of exactly this length was probably cut, so its last
# entry - and therefore the number of authors - cannot be trusted.
AUTORI_MAX_LENGTH = 1000

EXACT = 'exact'            # surname and given name both match
INITIAL = 'initial'        # surname matches, given name only by initial
AMBIGUOUS = 'ambiguous'    # more than one author of the paper matches
NOT_FOUND = 'not_found'    # no author of the paper matches
UNKNOWN = 'unknown'        # not computed yet

STATUS_CHOICES = [
    (UNKNOWN, 'Not computed'),
    (EXACT, 'Matched by full name'),
    (INITIAL, 'Matched by surname and initial'),
    (AMBIGUOUS, 'Several authors match'),
    (NOT_FOUND, 'Name not found in the author list'),
]
RESOLVED = (EXACT, INITIAL)


def _norm(text):
    """Lowercase, no accents, letters only: 'D’Amico-Rossi' -> 'd amico rossi'."""
    text = unicodedata.normalize('NFKD', text or '')
    text = ''.join(c for c in text if not unicodedata.combining(c)).lower()
    return ' '.join(re.sub(r'[^a-z]+', ' ', text).split())


def _match_quality(entry, first_name, last_name):
    """EXACT, INITIAL or None for one entry of the author list."""
    surname, given = _norm(last_name), _norm(first_name).split()
    if not surname:
        return None

    if ',' in entry:
        entry_surname, _, entry_given = entry.partition(',')
        if _norm(entry_surname) != surname:
            return None
        entry_given = _norm(entry_given).split()
    else:
        # "Mario Rossi": the surname is the tail of the entry.
        words = _norm(entry).split()
        tail = surname.split()
        if len(words) <= len(tail) or words[-len(tail):] != tail:
            return None
        entry_given = words[:-len(tail)]

    if not given or not entry_given:
        # Surname only on one side: weaker evidence, treat like an initial.
        return INITIAL
    if entry_given[0] == given[0]:
        return EXACT
    # "M." against "Mario", in either direction.
    if (len(entry_given[0]) == 1 or len(given[0]) == 1) and entry_given[0][0] == given[0][0]:
        return INITIAL
    return None


def find_position(autori, first_name, last_name):
    """Return (position, n_authors, status) for one person in one paper.

    position   1-based index in the author list, 0 when not resolved
    n_authors  length of the list, 0 when the stored string was truncated
    status     one of the constants above
    """
    entries = split_authors(autori)
    truncated = len(autori or '') >= AUTORI_MAX_LENGTH
    n_authors = 0 if truncated else len(entries)

    matches = []
    for index, entry in enumerate(entries, start=1):
        quality = _match_quality(entry, first_name, last_name)
        if quality:
            matches.append((index, quality))

    if not matches:
        return 0, n_authors, NOT_FOUND
    exact = [m for m in matches if m[1] == EXACT]
    if len(exact) == 1:
        return exact[0][0], n_authors, EXACT
    if len(matches) == 1:
        return matches[0][0], n_authors, matches[0][1]
    return 0, n_authors, AMBIGUOUS
