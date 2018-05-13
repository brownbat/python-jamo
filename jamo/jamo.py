# -*- coding: utf-8 -*-
"""Syllable and jamo analysis for Korean. Default internal exchange form is
Hangul characters, not codepoints. Jamo exchange form is U+11xx characters,
not U+3xxx Hangul Compatibility Jamo (HCJ) characters or codepoints.

For more information, see:
http://python-jamo.readthedocs.org/ko/latest/
"""

import os
from sys import stderr
from itertools import chain
import re
import unicodedata
import json


_ROOT = os.path.abspath(os.path.dirname(__file__))

_JAMO_OFFSET = 44032
_JAMO_LEAD_OFFSET = 0x10ff
_JAMO_VOWEL_OFFSET = 0x1160
_JAMO_TAIL_OFFSET = 0x11a7

with open(os.path.join(_ROOT, 'data', "U+11xx.json"), 'r') as namedata:
    _JAMO_DECOMPOSITION = json.load(namedata)
_JAMO_COMPOSITION = {name: char for char, name in _JAMO_DECOMPOSITION.items()}

hex_components_dictionary = _JAMO_DECOMPOSITION


JAMO_LEADS = [chr(_) for _ in range(0x1100, 0x115F)]
JAMO_LEADS_MODERN = [chr(_) for _ in range(0x1100, 0x1113)]
JAMO_VOWELS = [chr(_) for _ in range(0x1161, 0x11A8)]
JAMO_VOWELS_MODERN = [chr(_) for _ in range(0x1161, 0x1176)]
JAMO_TAILS = [chr(_) for _ in range(0x11A8, 0x1200)]
JAMO_TAILS_MODERN = [chr(_) for _ in range(0x11A8, 0x11C3)]

# See http://www.unicode.org/charts/PDF/U1100.pdf
valid_jamo = (chr(_) for _ in range(0x1100, 0x1200))
# See http://www.unicode.org/charts/PDF/U3130.pdf
valid_hcj = chain((chr(_) for _ in range(0x3131, 0x3164)),
                  (chr(_) for _ in range(0x3165, 0x318f)))
# See http://www.unicode.org/charts/PDF/UA960.pdf
valid_extA = (chr(_) for _ in range(0xa960, 0xa97d))
# See http://www.unicode.org/charts/PDF/UD7B0.pdf
valid_extB = chain((chr(_) for _ in range(0xd7b0, 0xd7c7)),
                   (chr(_) for _ in range(0xd7cb, 0xd7fc)))
valid_hangul = [chr(_) for _ in range(0xac00, 0xd7a4)]

class InvalidJamoError(Exception):
    """jamo is a U+11xx codepoint."""
    def __init__(self, message, jamo):
        super(InvalidJamoError, self).__init__(message)
        self.jamo = hex(ord(jamo))
        print("Could not parse jamo: U+{code}".format(code=self.jamo[2:]),
              file=stderr)


def _hangul_char_to_jamo(syllable):
    """Return a 3-tuple of lead, vowel, and tail jamo characters.
    Note: Non-Hangul characters are echoed back.
    """
    if is_hangul_char(syllable):
        rem = ord(syllable) - _JAMO_OFFSET
        tail = rem % 28
        vowel = 1 + ((rem - tail) % 588) // 28
        lead = 1 + rem // 588
        if tail:
            return (chr(lead + _JAMO_LEAD_OFFSET),
                    chr(vowel + _JAMO_VOWEL_OFFSET),
                    chr(tail + _JAMO_TAIL_OFFSET))
        else:
            return (chr(lead + _JAMO_LEAD_OFFSET),
                    chr(vowel + _JAMO_VOWEL_OFFSET))
    else:
        return syllable


def _jamo_to_hangul_char(lead, vowel, tail=0):
    """Return the Hangul character for the given jamo characters.
    """
    lead = ord(lead) - _JAMO_LEAD_OFFSET
    vowel = ord(vowel) - _JAMO_VOWEL_OFFSET
    tail = ord(tail) - _JAMO_TAIL_OFFSET if tail else 0
    return chr(tail + (vowel - 1) * 28 + (lead - 1) * 588 + _JAMO_OFFSET)


def _jamo_char_to_hcj(char):
    if is_jamo(char):
        hcj_name = re.sub("(?<=HANGUL )(\w+)",
                          "LETTER",
                          _get_unicode_name(char))
        try:
            return unicodedata.lookup(hcj_name)
        except KeyError:
            pass
    return char


def _get_unicode_name(char):
    """Fetch the unicode name for jamo characters.
    """
    return unicodedata.name(char)


def is_jamo(character):
    """Test if a single character is a jamo character.
    Valid jamo includes all modern and archaic jamo, as well as all HCJ.
    Non-assigned code points are invalid.
    """
    code = ord(character)
    return 0x1100 <= code <= 0x11FF or\
        0xA960 <= code <= 0xA97C or\
        0xD7B0 <= code <= 0xD7C6 or 0xD7CB <= code <= 0xD7FB or\
        is_hcj(character)


def is_jamo_modern(character):
    """Test if a single character is a modern jamo character.
    Modern jamo includes all U+11xx jamo in addition to HCJ in modern usage,
    as defined in Unicode 7.0.
    WARNING: U+1160 is NOT considered a modern jamo character, but it is listed
    under 'Medial Vowels' in the Unicode 7.0 spec.
    """
    code = ord(character)
    return 0x1100 <= code <= 0x1112 or\
        0x1161 <= code <= 0x1175 or\
        0x11A8 <= code <= 0x11C2 or\
        is_hcj_modern(character)


def is_hcj(character):
    """Test if a single character is a HCJ character.
    HCJ is defined as the U+313x to U+318x block, sans two non-assigned code
    points.
    """
    return 0x3131 <= ord(character) <= 0x318E and ord(character) != 0x3164


def is_hcj_modern(character):
    """Test if a single character is a modern HCJ character.
    Modern HCJ is defined as HCJ that corresponds to a U+11xx jamo character
    in modern usage.
    """
    code = ord(character)
    return 0x3131 <= code <= 0x314E or\
        0x314F <= code <= 0x3163


def is_hangul_char(character):
    """Test if a single character is in the U+AC00 to U+D7A3 code block,
    excluding unassigned codes.
    """
    return 0xAC00 <= ord(character) <= 0xD7A3


def is_jamo_compound(character):
    """Test if a single character is a compound, i.e., a consonant
    cluster, double consonant, or dipthong.

    COMPOUNDS:
    "-" in character_name  # clusters
    "SSANG" in character_name  # doubles
    "KAPYEOUN" in character_name  # kapyeouns
    "W" in character_name  # dipthongs
    # JUNGSEONG / LETTER OE (ᅬ) and YI (ᅴ)
    "YI" in character_name or "OE" in character_name
    "ARAEAE" in character_name:  # LETTER ARAEAE (ㆎ)

    NOTE: YEORINHIEU is NOT a compound, the bar indicates the glottal stop,
    like in consonants, but added to the null ㅇ, without the burst of
    aspiration from the extra dot in ㅎ.
    """
    if len(character) != 1:
        return False
        # Consider instead:
        # raise TypeError('is_jamo_compound() expected a single character')
    if is_jamo(character):
        # Once JAMO_COMPOUNDS is more comprehensive replace with:
        # return character in JAMO_COMPOUNDS
        character_name = unicodedata.name(character)
        if "-" in character_name:
            return True
        elif "SSANG" in character_name:
            return True
        elif "KAPYEOUN" in character_name:
            return True
        elif "W" in character_name:
            return True
        # JUNGSEONG/LETTER OE (ᅬ) and YI (ᅴ)
        elif "YI" in character_name or "OE" in character_name:
            return True
        # LETTER ARAEAE (ㆎ)
        elif "ARAEAE" in character_name:
            return True
    return False


def get_jamo_class(jamo):
    """Determine if a jamo character is a lead, vowel, or tail.
    Integers and U+11xx characters are valid arguments. HCJ consonants are not
    valid here.

    get_jamo_class should return the class ["lead" | "vowel" | "tail"] of a
    given character or integer.

    Note: jamo class directly corresponds to the Unicode 7.0 specification,
    thus includes filler characters as having a class.
    """
    # TODO: Perhaps raise a separate error for U+3xxx jamo.
    if jamo in JAMO_LEADS or jamo == chr(0x115F):
        return "lead"
    if jamo in JAMO_VOWELS or jamo == chr(0x1160) or\
            0x314F <= ord(jamo) <= 0x3163:
        return "vowel"
    if jamo in JAMO_TAILS:
        return "tail"
    else:
        raise InvalidJamoError("Invalid or classless jamo argument.", jamo)


def jamo_to_hcj(data):
    """Convert jamo to HCJ.
    Arguments may be iterables or single characters.

    jamo_to_hcj should convert every jamo character into HCJ in a given input,
    if possible. Anything else is unchanged.

    jamo_to_hcj is the generator version of j2hcj, the string version. Passing
    a character to jamo_to_hcj will still return a generator.
    """
    return (_jamo_char_to_hcj(_) for _ in data)


def j2hcj(jamo):
    """Convert jamo into HCJ.
    Arguments may be iterables or single characters.

    j2hcj should convert every jamo character into HCJ in a given input, if
    possible. Anything else is unchanged.

    j2hcj is the string version of jamo_to_hcj, the generator version.
    """
    return ''.join(jamo_to_hcj(jamo))


def hcj_to_jamo(hcj_char, position="vowel"):
    """Convert a HCJ character to a jamo character.
    Arguments may be single characters along with the desired jamo class
    (lead, vowel, tail). Non-mappable input will raise an InvalidJamoError.
    """
    if position == "lead":
        jamo_class = "CHOSEONG"
    elif position == "vowel":
        jamo_class = "JUNGSEONG"
    elif position == "tail":
        jamo_class = "JONGSEONG"
    else:
        raise InvalidJamoError("No mapping from input to jamo.", hcj_char)
    jamo_name = re.sub("(?<=HANGUL )(\w+)",
                       jamo_class,
                       _get_unicode_name(hcj_char))
    # TODO: add tests that test non entries.
    # if jamo_name in _JAMO_REVERSE_LOOKUP.keys():
    #     return _JAMO_REVERSE_LOOKUP[jamo_name]
    try:
        return unicodedata.lookup(jamo_name)
    except KeyError:
        return hcj_char


def hcj2j(hcj_char, position="vowel"):
    """Convert a HCJ character to a jamo character.
    Identical to hcj_to_jamo.
    """
    return hcj_to_jamo(hcj_char, position)


def hangul_to_jamo(hangul_string):
    """Convert a string of Hangul to jamo.
    Arguments may be iterables of characters.

    hangul_to_jamo should split every Hangul character into U+11xx jamo
    characters for any given string. Non-hangul characters are not changed.

    hangul_to_jamo is the generator version of h2j, the string version.
    """
    return (_ for _ in
            chain.from_iterable(_hangul_char_to_jamo(_) for _ in
                                hangul_string))


def h2j(hangul_string):
    """Convert a string of Hangul to jamo.
    Arguments may be iterables of characters.

    h2j should split every Hangul character into U+11xx jamo for any given
    string. Non-hangul characters are not touched.

    h2j is the string version of hangul_to_jamo, the generator version.
    """
    return ''.join(hangul_to_jamo(hangul_string))


def jamo_to_hangul(lead, vowel, tail=''):
    """Return the Hangul character for the given jamo input.
    Integers corresponding to U+11xx jamo codepoints, U+11xx jamo characters,
    or HCJ are valid inputs.

    Outputs a one-character Hangul string.

    This function is identical to j2h.
    """
    # Internally, we convert everything to a jamo char,
    # then pass it to _jamo_to_hangul_char
    lead = hcj_to_jamo(lead, "lead")
    vowel = hcj_to_jamo(vowel, "vowel")
    if not tail or ord(tail) == 0:
        tail = None
    elif is_hcj(tail):
        tail = hcj_to_jamo(tail, "tail")
    if (is_jamo(lead) and get_jamo_class(lead) == "lead") and\
       (is_jamo(vowel) and get_jamo_class(vowel) == "vowel") and\
       ((not tail) or (is_jamo(tail) and get_jamo_class(tail) == "tail")):
        result = _jamo_to_hangul_char(lead, vowel, tail)
        if is_hangul_char(result):
            return result
    raise InvalidJamoError("Could not synthesize characters to Hangul.",
                           '\x00')


def j2h(lead, vowel, tail=0):
    """Arguments may be integers corresponding to the U+11xx codepoints, the
    actual U+11xx jamo characters, or HCJ.

    Outputs a one-character Hangul string.

    This function is defined solely for naming conisistency with
    jamo_to_hangul.
    """
    return jamo_to_hangul(lead, vowel, tail)


def _decompose_jamo_to_hex(jamo):
    """Return a string of hex codepoints that make up a compound.

    WARNING: Some codepoints are mapped to other compounds in unexpected ways.
    To achieve a full canonical decomposition, call the recursive version of
    this function instead: _decompose_jamo_to_hex_recursive().

    Decompositions sourced from unicodedata.decomposition() and Auxiliary
    Hangul Decompositions 5.0.0d3, at https://
    www.unicode.org/L2/L2006/06310-AuxiliaryHangulDecompositions-5.0.0d3.txt

    Note: An empty string is returned if no decomposition is available.
    InvalidJamoError will be raised if 'jamo' is not a jamo character.
    """
    components_string = ""
    if not is_jamo(jamo):
        raise InvalidJamoError("Invalid jamo argument.", jamo)
    codepoint = str(hex(ord(jamo)))[2:].upper()
    components_string = unicodedata.decomposition(jamo)
    if components_string == '':
        components_string = hex_components_dictionary.get(codepoint, '')
    return components_string


def _decompose_jamo_to_hex_recursive(jamo):
    """Return a string of hex codepoints that make up a compound.

    Decompositions sourced from unicodedata.decomposition() and Auxiliary
    Hangul Decompositions 5.0.0d3, at https://
    www.unicode.org/L2/L2006/06310-AuxiliaryHangulDecompositions-5.0.0d3.txt

    Note: An empty string is returned if no decomposition is available.
    InvalidJamoError will be raised if 'jamo' is not a jamo character.
    """
    decomposition = ""
    for component in _decompose_jamo_to_hex(jamo).split():
        if len(decomposition) > 0:
            decomposition += ' '
        if component[0] == '<':
            decomposition += component
        else:
            intermediate_decomposition = _decompose_jamo_to_hex_recursive(
                    chr(int(component, 16)))
            if intermediate_decomposition == '':
                decomposition += component
            else:
                decomposition += intermediate_decomposition
    return decomposition


def decompose_jamo(jamo, verbose=False, strict=False):
    """Return a tuple of characters that make up a jamo compound.

    Setting verbose to True will include the unicode notations in the
    decomposition, such as "<free>" or "<circle>".

    The character will be echoed back if no decomposition is available.
    InvalidJamoError will be raised if 'jamo' is not a jamo character.
    Setting strict to True will also cause InvalidJamoError to be raised if no
    decomposition is found.

    Decompositions sourced from unicodedata.decomposition() and Auxiliary
    Hangul Decompositions 5.0.0d3, at https://
    www.unicode.org/L2/L2006/06310-AuxiliaryHangulDecompositions-5.0.0d3.txt
    """
    if not is_jamo(jamo):
        raise InvalidJamoError("Invalid jamo argument.", jamo)
    hex_components = _decompose_jamo_to_hex_recursive(jamo)
    character_components = []
    for hex_component in hex_components.split():
        if hex_component[0] == '<':
            character_components.append(hex_component)
        else:
            tmp_jamo = chr(int(hex_component, 16))
            if not is_jamo(tmp_jamo):
                raise InvalidJamoError("Invalid jamo from lookup in \
                                       _decompose_jamo_to_hex().", jamo)
            else:
                character_components.append(tmp_jamo)
    # Correct unexpected character class switching
    jamo_class = unicodedata.name(jamo).split()[1]
    for idx in range(len(character_components)):
        component = character_components[idx]
        if component[0] != '<':
            if unicodedata.name(component).split()[1] != jamo_class:
                test_component_name = unicodedata.name(component).split()
                test_component_name[1] = jamo_class
                try:
                    test_component = unicodedata.lookup(
                            " ".join(test_component_name))
                    character_components[idx] = test_component
                except KeyError:
                    # If we can't match class anyway, doesn't matter.
                    pass
    if not verbose:
        to_strip = []
        for component in character_components:
            if len(component) != 1:
                to_strip.append(component)
            elif not is_jamo(component):
                to_strip.append(component)
            elif hex(ord(component)) in ['0x1160', '0x115F']:
                to_strip.append(component)
        for component in to_strip:
            character_components.remove(component)
    # Echoes character back if nothing found. Should we always return a tuple?
    if len(character_components) == 0:
        character_components = jamo
    elif len(character_components) == 1:
        character_components = character_components[0]
    else:
        character_components = tuple(character_components)
    # Final test for SSANG and hyphen compositions not caught by Aux Decomps
    if character_components == jamo:
        jamo_name = unicodedata.name(jamo)
        if ('SSANG' in jamo_name or '-' in jamo_name and jamo_name !=
                "HANGUL SYLLABLE SSANG"):
            assert len(jamo_name.split()) == 3
            prefix = " ".join(jamo_name.split()[:2])
            forms = [jamo_name.split()[-1]]
            while 'SSANG' in ''.join(forms) or '-' in ''.join(forms):
                for part in forms:
                    if '-' in part:
                        forms.remove(part)
                        forms.extend(part.split('-'))
                        break
                    if 'SSANG' in part:
                        forms.remove(part)
                        part = part.replace('SSANG', '')
                        forms.extend([part]*2)
                        break
            character_components = []
            for form in forms:
                character_components.append(unicodedata.lookup(prefix + ' ' +
                                            form))
    if strict:
        if character_components == jamo:
            raise InvalidJamoError("No decomposition found for jamo.", jamo)
    return character_components


def compose_jamo(*parts):
    """Return the compound jamo for the given jamo input.
    Integers corresponding to U+11xx jamo codepoints, U+11xx jamo
    characters, or HCJ are valid inputs.

    Outputs a one-character jamo string.

    WARNING: Archaic jamo compounds not implemented, will raise
    InvalidJamoError.
    """
    # Internally, we convert everything to a jamo char,
    # then pass it to _jamo_to_hangul_char
    # NOTE: Relies on hcj_to_jamo not strictly requiring "position" arg.
    for p in parts:
        if not (type(p) == str and len(p) == 1 and 2 <= len(parts) <= 3):
            raise TypeError("compose_jamo() expected 2-3 single characters " +
                            "but received " + str(parts),
                            '\x00')
    hcparts = [j2hcj(_) for _ in parts]
    for compound, dict_parts in JAMO_COMPOUNDS_MODERN_DICTIONARY.items():
        hcdict_parts = [j2hcj(_) for _ in dict_parts]
        if hcparts == hcdict_parts and is_jamo(compound):
            return compound
    raise InvalidJamoError(
            "Could not synthesize characters to compound: " + ", ".join(
                    str(_) + "(U+" + str(hex(ord(_)))[2:] +
                    ")" for _ in parts), '\x00')


def synth_hangul(string):
    """Convert jamo characters in a string into hcj as much as possible."""
    raise NotImplementedError
    return ''.join([''.join(''.join(jamo_to_hcj(_)) for _ in string)])
