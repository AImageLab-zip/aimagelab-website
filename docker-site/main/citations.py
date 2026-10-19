"""BibTeX and APA rendering for IRIS publications.

IRIS gives us Italian type labels ("Articolo su rivista", "Relazione in Atti
di Convegno", ...) and a single `autori` string, so both renderers work from
those rather than from structured author records.
"""
import re
import unicodedata

# IRIS type label -> BibTeX entry type. Matched case-insensitively on a
# substring, because the labels vary ("Relazione in Atti di Convegno",
# "Abstract in Atti di Convegno").
_ENTRY_TYPES = (
    ('atti di convegno', 'inproceedings'),
    ('articolo su rivista', 'article'),
    ('abstract in rivista', 'article'),
    ('capitolo', 'incollection'),
    ('saggio', 'incollection'),
    ('curatela', 'book'),
    ('monografia', 'book'),
    ('trattato', 'book'),
    ('tesi di dottorato', 'phdthesis'),
    ('brevetto', 'misc'),
    ('poster', 'misc'),
)


def entry_type(pub):
    label = (pub.tipo or '').lower()
    for needle, bib in _ENTRY_TYPES:
        if needle in label:
            return bib
    return 'misc'


def split_authors(autori):
    """IRIS stores authors as 'Rossi, Mario; Bianchi, Anna' in one string."""
    if not autori:
        return []
    parts = [a.strip(' .') for a in re.split(r'\s*;\s*', autori) if a.strip(' .')]
    return parts


def _ascii_key(text):
    """Strip accents for the citation key: BibTeX keys must stay ASCII."""
    norm = unicodedata.normalize('NFKD', text or '')
    return ''.join(c for c in norm if not unicodedata.combining(c))


def cite_key(pub):
    """A stable, collision-resistant key: surnameYEARfirstword."""
    authors = split_authors(pub.autori)
    surname = authors[0].split(',')[0] if authors else 'anon'
    surname = re.sub(r'[^A-Za-z]', '', _ascii_key(surname)).lower() or 'anon'
    # Skip leading articles so keys are "milic2026multidisciplinary", not
    # "milic2026a" - otherwise most English titles collide on "a"/"the".
    stop = {'a', 'an', 'the', 'on', 'of', 'in', 'for', 'and', 'to'}
    first_word = ''
    for word in re.split(r'\s+', pub.titolo or ''):
        clean = re.sub(r'[^A-Za-z]', '', _ascii_key(word)).lower()
        if clean and clean not in stop:
            first_word = clean
            break
    return f"{surname}{pub.anno or 'nd'}{first_word}"[:60]


def _venue(pub):
    """Journal for articles, conference for proceedings."""
    if 'convegno' in (pub.tipo or '').lower():
        return pub.conferenza or pub.rivista or ''
    return pub.rivista or ''


def _escape_bibtex(value):
    # Only the characters that actually break a .bib file.
    return (str(value).replace('\\', r'\textbackslash{}')
            .replace('{', r'\{').replace('}', r'\}')
            .replace('&', r'\&').replace('%', r'\%')
            .replace('$', r'\$').replace('#', r'\#')
            .replace('_', r'\_'))


def to_bibtex(pub):
    etype = entry_type(pub)
    venue_field = 'booktitle' if etype in ('inproceedings', 'incollection') else 'journal'
    fields = [
        ('author', ' and '.join(split_authors(pub.autori))),
        ('title', pub.titolo),
        (venue_field, _venue(pub)),
        ('year', pub.anno),
        ('volume', pub.volume),
        ('number', pub.numero),
        ('pages', (pub.pagine or '').replace('-', '--')),
        ('publisher', pub.editore),
        ('address', pub.luogo),
        ('doi', pub.doi),
        ('issn', pub.issn),
        ('isbn', pub.isbn),
        ('url', pub.url or (f'https://doi.org/{pub.doi}' if pub.doi else '')),
    ]
    if etype == 'phdthesis':
        fields = [(k, v) for k, v in fields if k not in ('journal', 'booktitle')]
    lines = [f'@{etype}{{{cite_key(pub)},']
    for key, value in fields:
        if value in (None, '', 0):
            continue
        # doi/url are verbatim identifiers: escaping "_" there yields a DOI
        # that no longer resolves when copied out of the .bib.
        rendered = value if key in ('doi', 'url') else _escape_bibtex(value)
        lines.append(f'  {key} = {{{rendered}}},')
    if len(lines) > 1:
        lines[-1] = lines[-1].rstrip(',')
    lines.append('}')
    return '\n'.join(lines)


def _apa_authors(autori):
    """'Rossi, Mario' -> 'Rossi, M.'; join per APA rules."""
    out = []
    for a in split_authors(autori):
        if ',' in a:
            last, _, first = a.partition(',')
            initials = ' '.join(f'{p[0]}.' for p in first.split() if p and p[0].isalpha())
            out.append(f'{last.strip()}, {initials}'.strip().rstrip(','))
        else:
            out.append(a)
    if not out:
        return ''
    if len(out) == 1:
        return out[0]
    if len(out) > 20:
        return ', '.join(out[:19]) + ', ... ' + out[-1]
    return ', '.join(out[:-1]) + ', & ' + out[-1]


def to_apa(pub):
    bits = [_apa_authors(pub.autori)]
    bits.append(f'({pub.anno}).' if pub.anno else '(n.d.).')
    title = (pub.titolo or '').strip().rstrip('.')
    bits.append(f'{title}.')
    venue = _venue(pub)
    if venue:
        tail = venue
        if pub.volume:
            tail += f', {pub.volume}'
            if pub.numero:
                tail += f'({pub.numero})'
        if pub.pagine:
            tail += f', {pub.pagine}'
        bits.append(f'{tail}.')
    if pub.editore and entry_type(pub) in ('book', 'incollection', 'phdthesis'):
        bits.append(f'{pub.editore}.')
    if pub.doi:
        bits.append(f'https://doi.org/{pub.doi}')
    elif pub.url:
        bits.append(pub.url)
    return ' '.join(b for b in bits if b).strip()
