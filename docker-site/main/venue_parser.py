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
_ACRONYM_TAIL = re.compile(r',\s*([A-Z][A-Za-z0-9/&+-]{1,14})\s+((?:19|20)\d{2})\b')
# "(BMVC)" or "(BMVC 2025)". Checked only after the tail form, because the
# citation usually ends with a LOCATION parenthetical - "(USA)", "(UK)" -
# which would otherwise win and label every venue with a country.
_ACRONYM_PAREN = re.compile(r'\(([A-Z][A-Za-z0-9/&+-]{1,14})(?:\s+(?:19|20)\d{2})?\)')
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
            if cand.upper() not in _NOT_ACRONYMS and not cand.isdigit():
                return cand
    # No usable acronym: text up to the first comma, minus any trailing year
    # and any leading ordinal ("19th European Conference..." -> same key as
    # "20th European Conference...").
    head = venue.split(',')[0]
    head = re.sub(r'\s*(19|20)\d{2}\s*$', '', head).strip()
    head = re.sub(r'^\s*\d+(st|nd|rd|th)?[.\s]+', '', head, flags=re.I)
    return re.sub(r'\s+', ' ', head)[:120].strip()
