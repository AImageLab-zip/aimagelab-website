"""Extract the conference/venue from an IRIS citation string.

IRIS's /products endpoint returns no conference field at all (and
/products;full is a 500), so for 'Relazione in Atti di Convegno' the venue
survives only inside `citation`, as the last parenthetical group:

  TITLE / AUTHORS. - (2026), pp. 760-770. (13th International Conference on
  3D Vision, 3DV 2026 can 2026) [10.1109/3dv69130.2026.00078].

Note the trailing [DOI], which is why a naive "parenthesis at end of string"
regex misses more than half of them.
"""
import re

_YEAR = re.compile(r'^\s*(19|20)\d{2}\s*$')
_PAGES = re.compile(r'^\s*(pp?\.|pag)', re.I)
# "Name, ACRONYM 2026" / "Name (BMVC)" -> the acronym is the useful short key
# "Name, ACRONYM 2026" -> the acronym is the useful short key.
# Acronyms may start with a digit ("3DV", "4DV"), so the first character is
# [A-Z0-9]; a letter is still required somewhere so a bare year cannot match.
_ACRONYM_TAIL = re.compile(r',\s*([A-Z0-9][A-Za-z0-9/&+-]{1,14})\s+((?:19|20)\d{2})\b')
# "(BMVC)" or "(BMVC 2025)". Checked only after the tail form, because the
# citation usually ends with a LOCATION parenthetical - "(USA)", "(UK)" -
# which would otherwise win and label every venue with a country.
_ACRONYM_PAREN = re.compile(r'\(([A-Z0-9][A-Za-z0-9/&+-]{1,14})(?:\s+(?:19|20)\d{2})?\)')
# Place names that look like acronyms and must never be used as a venue key.
_NOT_ACRONYMS = {
    'USA', 'US', 'UK', 'UAE', 'ITA', 'ITALY', 'JPN', 'JAPAN', 'CAN', 'CANADA',
    'DEU', 'GER', 'FRA', 'ESP', 'PRT', 'NLD', 'AUT', 'AUSTRIA', 'CHE', 'SWE',
    'GRC', 'POL', 'CZE', 'HUN', 'IRL', 'ISR', 'IND', 'CHN', 'KOR', 'AUS',
    'BRA', 'MEX', 'RUS', 'TUR', 'EU', 'CO', 'CA', 'NY', 'DC', 'TX', 'FL', 'WA',
}


def _top_level_groups(text):
    """Return the contents of every balanced top-level (...) group."""
    out, depth, start = [], 0, None
    for i, ch in enumerate(text):
        if ch == '(':
            if depth == 0:
                start = i + 1
            depth += 1
        elif ch == ')':
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    out.append(text[start:i])
                    start = None
    return out


def extract_venue(citation):
    """Full venue string, or '' when the citation carries none."""
    if not citation:
        return ''
    text = citation.strip()
    # Drop a trailing [doi] so the venue group is the last one.
    text = re.sub(r'\s*\[[^\]]*\]\s*\.?\s*$', '', text)
    candidates = [g.strip() for g in _top_level_groups(text)]
    # Walk backwards: the venue is the last group that is not a bare year or
    # a page range.
    for g in reversed(candidates):
        if not g or _YEAR.match(g) or _PAGES.match(g):
            continue
        if len(g) < 10:
            continue
        return re.sub(r'\s+', ' ', g).strip(' .,;')
    return ''


def short_name(venue):
    """A stable, groupable key for the filter dropdown."""
    if not venue:
        return ''
    for rx in (_ACRONYM_TAIL, _ACRONYM_PAREN):
        for m in rx.finditer(venue):
            cand = m.group(1)
            if cand.upper() not in _NOT_ACRONYMS and any(c.isalpha() for c in cand):
                return cand
    # No usable acronym: text up to the first comma, minus any trailing year
    # and any leading ordinal ("19th European Conference..." -> same key as
    # "20th European Conference...").
    head = venue.split(',')[0]
    head = re.sub(r'\s*(19|20)\d{2}\s*$', '', head).strip()
    head = re.sub(r'^\s*\d+(st|nd|rd|th)?[.\s]+', '', head, flags=re.I)
    return re.sub(r'\s+', ' ', head)[:120].strip()


# Month names and date fragments that mark the end of the conference name and
# the start of "where and when", which we do not want in a venue label.
_MONTHS = (r'jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|'
           r'january|february|march|april|june|july|august|september|october|'
           r'november|december|gennaio|febbraio|marzo|aprile|maggio|giugno|'
           r'luglio|agosto|settembre|ottobre|novembre|dicembre')
_TAIL_DATE = re.compile(
    r'\s*(?:[,(]\s*)?(?:\b(?:' + _MONTHS + r')\b|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|'
    r'\b\d{1,2}\s*[-–]\s*\d{1,2}\b).*$', re.I)
_LEADING_ORDINAL = re.compile(r'^\s*\d+\s*(?:st|nd|rd|th|°|a)?[.\s]+', re.I)
_TRAILING_YEAR = re.compile(r'[\s,]*\b(?:19|20)\d{2}\b[\s,.]*$')


_COUNTRIES = {
    'italy', 'italia', 'france', 'francia', 'germany', 'germania', 'spain',
    'spagna', 'portugal', 'austria', 'switzerland', 'svizzera', 'sweden',
    'svezia', 'norway', 'denmark', 'finland', 'netherlands', 'belgium',
    'greece', 'grecia', 'poland', 'polonia', 'czech republic', 'hungary',
    'ungheria', 'ireland', 'israel', 'india', 'china', 'cina', 'japan',
    'giappone', 'korea', 'south korea', 'australia', 'brazil', 'brasile',
    'mexico', 'canada', 'russia', 'turkey', 'united kingdom', 'uk',
    'united states', 'united states of america', 'usa', 'u.s.a.', 'uae',
    'singapore', 'slovenia', 'croatia', 'romania', 'serbia', 'scotland',
}
# A name is only trimmed back past a city if what remains still looks like a
# venue - otherwise "...on Computer Vision" would lose "Vision", which is a
# capitalised word but obviously part of the name.
_CONNECTIVES = {'on', 'in', 'of', 'and', 'for', 'the', 'to', 'at', 'a', 'su', 'di', 'e'}
_VENUE_WORD = re.compile(
    r'\b(conference|conferences|workshop|workshops|symposium|congress|meeting|'
    r'convention|summit|school|forum|convegno|conf\.)\b', re.I)


_US_STATE = re.compile(r'^[A-Z]{2}$')


def _strip_place(name):
    """Remove a trailing "City[, ST], Country" that the citation appended.

    Only one token is removed for the city, unless a US state code was also
    present - "Las Vegas, NV, United States" - in which case the city may be
    two tokens. An earlier version looped freely and chewed "European
    Conference on Computer Vision Malmo" back to "European Conference on".
    """
    parts = [p.strip() for p in name.split(',')]
    if len(parts) < 2 or parts[-1].lower().strip('. ') not in _COUNTRIES:
        return name

    parts = parts[:-1]                       # drop the country
    had_state = False
    while len(parts) > 1 and _US_STATE.match(parts[-1]):
        parts = parts[:-1]                   # drop "NV" / "CA"
        had_state = True

    head = ','.join(parts).strip()
    words = head.split()
    for _ in range(2 if had_state else 1):
        if len(words) > 2 and words[-1][:1].isupper():
            trimmed = words[:-1]
            # A dangling connective means we cut into the name, not the city.
            if trimmed[-1].lower() in _CONNECTIVES:
                break
            words = trimmed
        else:
            break
    return ' '.join(words).strip(' ,')


def display_name(venue):
    """Human-readable venue label: full conference name, acronym in brackets.

    The stored venue is the raw citation fragment - "20th International
    Conference on Document Analysis and Recognition, ICDAR 2026 Vienna,
    AUSTRIA AUG 30-SEP 04, 2026" - which is far too noisy to show on a card.
    """
    if not venue:
        return ''
    text = re.sub(r'\s+', ' ', venue).strip()

    acronym = ''
    # "Name, ACRONYM 2026 <place> <dates>" - cut at the acronym.
    m = _ACRONYM_TAIL.search(text)
    if m and m.group(1).upper() not in _NOT_ACRONYMS and any(c.isalpha() for c in m.group(1)):
        acronym = m.group(1)
        name = text[:m.start()]
    else:
        # "Name (ACRONYM) <place> <dates>" - cut after the bracket.
        m = _ACRONYM_PAREN.search(text)
        if m and m.group(1).upper() not in _NOT_ACRONYMS and any(c.isalpha() for c in m.group(1)):
            acronym = m.group(1)
            name = text[:m.start()]
        else:
            name = text

    name = _TAIL_DATE.sub('', name)
    name = _TRAILING_YEAR.sub('', name)
    name = _strip_place(name)
    name = _LEADING_ORDINAL.sub('', name)
    name = name.strip(' ,.-–;')

    if not name:
        return acronym or text[:120]
    if acronym and acronym.lower() not in name.lower():
        return f'{name} ({acronym})'
    return name
