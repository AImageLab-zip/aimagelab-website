"""Text clean-up for names coming from LDAP."""
import re

# "Niccolò" stored double-encoded reads back as "NiccolÃ²": each UTF-8 byte
# of the accented letter (0xC3 0xB2) was taken for a Latin-1 character and
# encoded again. A lead byte 0xC2-0xDF followed by a continuation byte
# 0x80-0xBF is the signature of one mis-decoded two-byte sequence.
_MOJIBAKE = re.compile('[Â-ß][\u0080-¿]')

# The old importer then ran str.capitalize() on the name, which lowercases
# the lead byte (Ã -> ã, Â -> â ...) and hides the signature: "Niccolã²".
# Lowercase lead bytes are only undone in front of a character that cannot
# follow a real letter in a name (0x80-0xBF holds symbols such as ² ¨ © ±).
_LOWERED = re.compile('[â-ÿ](?=[\u0080-¿])')


def _redecode(text):
    for codec in ('cp1252', 'latin-1'):
        try:
            return text.encode(codec).decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
    return None


def repair_mojibake(text):
    """Undo UTF-8 text that was decoded as Latin-1 and stored again.

    Returns the input unchanged unless it carries the signature above AND
    the whole string converts back cleanly, so correctly stored names
    ("José", "Müller", "Niccolò") are never touched.
    """
    if not text:
        return text
    candidate = text
    if not _MOJIBAKE.search(candidate):
        # Maybe the lead byte was lowercased by the old capitalize().
        candidate = _LOWERED.sub(lambda m: m.group(0).upper(), text)
        if not _MOJIBAKE.search(candidate):
            return text
    repaired = _redecode(candidate)
    return repaired if repaired is not None else text


def name_case(text):
    """Capitalise a personal name: "NICCOLÒ D'AMICO" -> "Niccolò D'Amico".

    str.capitalize() per word turned "D'AMICO" into "D'amico" and
    "ANNA-MARIA" into "Anna-maria"; this also capitalises after an
    apostrophe or a hyphen.
    """
    if not text:
        return ''
    return ' '.join(
        re.sub(r"(^|['’\-])(\w)", lambda m: m.group(1) + m.group(2).upper(), word.lower())
        for word in text.split()
    )
