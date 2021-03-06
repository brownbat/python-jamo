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
import json
import re
import unicodedata


_ROOT = os.path.abspath(os.path.dirname(__file__))

_JAMO_OFFSET = 44032
_JAMO_LEAD_OFFSET = 0x10ff
_JAMO_VOWEL_OFFSET = 0x1160
_JAMO_TAIL_OFFSET = 0x11a7

with open(os.path.join(_ROOT, 'data', "U+11xx.json"), 'r') as namedata:
    _JAMO_TO_NAME = json.load(namedata)
_JAMO_REVERSE_LOOKUP = {name: char for char, name in _JAMO_TO_NAME.items()}
with open(os.path.join(_ROOT, 'data', "U+31xx.json"), 'r') as namedata:
    _HCJ_TO_NAME = json.load(namedata)
_HCJ_REVERSE_LOOKUP = {name: char for char, name in _HCJ_TO_NAME.items()}

JAMO_LEADS = [chr(_) for _ in range(0x1100, 0x115F)]
JAMO_LEADS_MODERN = [chr(_) for _ in range(0x1100, 0x1113)]
JAMO_VOWELS = [chr(_) for _ in range(0x1161, 0x11A8)]
JAMO_VOWELS_MODERN = [chr(_) for _ in range(0x1161, 0x1176)]
JAMO_TAILS = [chr(_) for _ in range(0x11A8, 0x1200)]
JAMO_TAILS_MODERN = [chr(_) for _ in range(0x11A8, 0x11C3)]

# Hangul letters
JAMO_DOUBLE_CONSONANTS_MODERN = ["ㄲ", "ㄸ", "ㅃ", "ㅆ", "ㅉ"]
JAMO_CONSONANT_CLUSTERS_MODERN = ["ㄳ", "ㄵ", "ㄶ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ",
                                  "ㄿ", "ㅀ", "ㅄ"]
JAMO_DIPTHONGS_MODERN = ["ㅘ", "ㅙ", "ㅚ", "ㅝ", "ㅞ", "ㅟ", "ㅢ"]

# Positional forms
JAMO_POSITIONAL_DOUBLE_CONSONANTS = [
        "ᄁ", "ᄄ", "ᄈ", "ᄊ", "ᄍ", "ᄔ", "ᄙ", "ᄥ", "ᄬ", "ᄴ", "ᄽ", "ᄿ",
        "ᅇ", "ᅏ", "ᅑ", "ᅘ", "ᆢ", "ᆩ", "ᆻ", "ᇐ", "ᇖ", "ᇞ", "ᇭ", "ᇮ",
        "ᇿ"]
JAMO_POSITIONAL_CLUSTERS = [
        "ᄓ", "ᄕ", "ᄖ", "ᄗ", "ᄘ", "ᄚ", "ᄜ", "ᄞ", "ᄟ", "ᄠ", "ᄡ", "ᄢ",
        "ᄣ", "ᄤ", "ᄥ", "ᄦ", "ᄧ", "ᄨ", "ᄩ", "ᄪ", "ᄭ", "ᄮ", "ᄯ", "ᄰ",
        "ᄱ", "ᄲ", "ᄳ", "ᄴ", "ᄵ", "ᄶ", "ᄷ", "ᄸ", "ᄹ", "ᄺ", "ᄻ", "ᅁ",
        "ᅂ", "ᅃ", "ᅄ", "ᅅ", "ᅆ", "ᅈ", "ᅉ", "ᅊ", "ᅋ", "ᅍ", "ᅒ", "ᅓ",
        "ᅖ", "ᅚ", "ᅛ", "ᅜ", "ᅝ", "ᅞ", "ᅶ", "ᅷ", "ᅸ", "ᅹ", "ᅺ", "ᅻ",
        "ᅼ", "ᅽ", "ᅾ", "ᅿ", "ᆀ", "ᆁ", "ᆂ", "ᆃ", "ᆄ", "ᆅ", "ᆆ", "ᆇ",
        "ᆈ", "ᆉ", "ᆊ", "ᆋ", "ᆌ", "ᆍ", "ᆎ", "ᆏ", "ᆐ", "ᆑ", "ᆒ", "ᆓ",
        "ᆔ", "ᆕ", "ᆖ", "ᆗ", "ᆘ", "ᆙ", "ᆚ", "ᆛ", "ᆜ", "ᆝ", "ᆟ", "ᆠ",
        "ᆡ", "ᆣ", "ᆤ", "ᆥ", "ᆦ", "ᆧ", "ᆪ", "ᆬ", "ᆭ", "ᆰ", "ᆱ", "ᆲ",
        "ᆳ", "ᆴ", "ᆵ", "ᆶ", "ᆹ", "ᇃ", "ᇄ", "ᇅ", "ᇆ", "ᇇ", "ᇈ", "ᇉ",
        "ᇊ", "ᇋ", "ᇌ", "ᇍ", "ᇎ", "ᇏ", "ᇑ", "ᇒ", "ᇓ", "ᇔ", "ᇕ", "ᇖ",
        "ᇗ", "ᇘ", "ᇙ", "ᇚ", "ᇛ", "ᇜ", "ᇝ", "ᇞ", "ᇟ", "ᇠ", "ᇡ", "ᇣ",
        "ᇤ", "ᇥ", "ᇧ", "ᇨ", "ᇩ", "ᇪ", "ᇬ", "ᇭ", "ᇯ", "ᇱ", "ᇲ", "ᇳ",
        "ᇵ", "ᇶ", "ᇷ", "ᇸ", "ᇺ", "ᇻ", "ᇼ", "ᇽ", "ᇾ"]
JAMO_POSITIONAL_DIPTHONGS = [
        "ᅪ", "ᅫ", "ᅯ", "ᅰ", "ᅱ", "ᄛ", "ᄝ", "ᄫ", "ᄬ", "ᅗ", "ᇕ", "ᇢ",
        "ᇦ", "ᇴ", "ᅙ", "ᇙ", "ᇹ", "ᅬ", "ᅴ", "ᆗ"]
JAMO_POSITIONAL_COMPOUNDS = JAMO_POSITIONAL_DOUBLE_CONSONANTS +\
                            JAMO_POSITIONAL_CLUSTERS +\
                            JAMO_POSITIONAL_DIPTHONGS

JAMO_COMPOUNDS_MODERN = JAMO_DOUBLE_CONSONANTS_MODERN +\
                        JAMO_CONSONANT_CLUSTERS_MODERN + JAMO_DIPTHONGS_MODERN
JAMO_COMPOUNDS_MODERN_DICTIONARY = {
        "ㄲ": ("ㄱ", "ㄱ"), "ㄸ": ("ㄷ", "ㄷ"), "ㅃ": ("ㅂ", "ㅂ"),
        "ㅆ": ("ㅅ", "ㅅ"), "ㅉ": ("ㅈ", "ㅈ"), "ㄳ": ("ㄱ", "ㅅ"),
        "ㄵ": ("ㄴ", "ㅈ"), "ㄶ": ("ㄴ", "ㅎ"), "ㄺ": ("ㄹ", "ㄱ"),
        "ㄻ": ("ㄹ", "ㅁ"), "ㄼ": ("ㄹ", "ㅂ"), "ㄽ": ("ㄹ", "ㅅ"),
        "ㄾ": ("ㄹ", "ㅌ"), "ㄿ": ("ㄹ", "ㅍ"), "ㅀ": ("ㄹ", "ㅎ"),
        "ㅄ": ("ㅂ", "ㅅ"), "ㅘ": ("ㅗ", "ㅏ"), "ㅙ": ("ㅗ", "ㅐ"),
        "ㅚ": ("ㅗ", "ㅣ"), "ㅝ": ("ㅜ", "ㅓ"), "ㅞ": ("ㅜ", "ㅔ"),
        "ㅟ": ("ㅜ", "ㅣ"), "ㅢ": ("ㅡ", "ㅣ")}

JAMO_DOUBLE_CONSONANTS_ARCHAIC = ["ㅥ", "ᄙ", "ㅹ", "ᄽ", "ᄿ", "ᅇ", "ᇮ", "ᅏ",
                                  "ᅑ", "ㆅ"]
JAMO_TWO_CONSONANT_CLUSTERS_ARCHAIC = [
        "ᇃ", "ᄓ", "ㅦ", "ᄖ", "ㅧ", "ㅨ", "ᇉ", "ᄗ", "ᇋ", "ᄘ", "ㅪ", "ㅬ",
        "ᇘ", "ㅭ", "ᇚ", "ᇛ", "ㅮ", "ㅯ", "ㅰ", "ᇠ", "ᇡ", "ㅲ", "ᄟ", "ㅳ",
        "ᇣ", "ㅶ", "ᄨ", "ㅷ", "ᄪ", "ᇥ", "ㅺ", "ㅻ", "ㅼ", "ᄰ", "ᄱ", "ㅽ",
        "ᄵ", "ㅾ", "ᄷ", "ᄸ", "ᄹ", "ᄺ", "ᄻ", "ᅁ", "ᅂ", "ᅃ", "ᅄ", "ᅅ",
        "ᅆ", "ᅈ", "ᅉ", "ᅊ", "ᅋ", "ᇬ", "ᇭ", "ㆂ", "ㆃ", "ᇯ", "ᅍ", "ᅒ",
        "ᅓ", "ᅖ", "ᇵ", "ᇶ", "ᇷ", "ᇸ"]
JAMO_THREE_CONSONANT_CLUSTERS_ARCHAIC = ["ᇄ", "ㅩ", "ᇏ", "ᇑ", "ᇒ", "ㅫ",
                                         "ᇔ", "ᇕ", "ᇖ", "ᇞ", "ㅴ", "ㅵ",
                                         "ᄤ", "ᄥ", "ᄦ", "ᄳ", "ᄴ"]
JAMO_CONSONANT_CLUSTERS_ARCHAIC = JAMO_TWO_CONSONANT_CLUSTERS_ARCHAIC +\
                                  JAMO_THREE_CONSONANT_CLUSTERS_ARCHAIC
JAMO_DIPTHONGS_ARCHAIC = [
        "ᆜ", "ᆝ", "ᆢ", "ᅷ", "ᅸ", "ᅹ", "ᅺ", "ᅻ", "ᅼ", "ᅽ", "ᅾ", "ᅿ",
        "ᆀ", "ᆁ", "ᆂ", "ᆃ", "ㆇ", "ㆈ", "ᆆ", "ᆇ", "ㆉ", "ᆉ", "ᆊ", "ᆋ",
        "ᆌ", "ᆍ", "ᆎ", "ᆏ", "ᆐ", "ㆊ", "ㆋ", "ᆓ", "ㆌ", "ᆕ", "ᆖ", "ᆗ",
        "ᆘ", "ᆙ", "ᆚ", "ᆛ", "ᆟ", "ᆠ", "ㆎ"]
JAMO_COMPOUNDS_ARCHAIC = JAMO_CONSONANT_CLUSTERS_ARCHAIC +\
                         JAMO_DIPTHONGS_ARCHAIC
JAMO_COMPOUNDS = JAMO_COMPOUNDS_MODERN + JAMO_COMPOUNDS_ARCHAIC


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
        if hcj_name in _HCJ_REVERSE_LOOKUP.keys():
            return _HCJ_REVERSE_LOOKUP[hcj_name]
    return char


def _get_unicode_name(char):
    """Fetch the unicode name for jamo characters.
    """
    if char not in _JAMO_TO_NAME.keys() and char not in _HCJ_TO_NAME.keys():
        raise InvalidJamoError("Not jamo or nameless jamo character", char)
    else:
        if is_hcj(char):
            return _HCJ_TO_NAME[char]
        return _JAMO_TO_NAME[char]


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
        # CHOSEONG YEORINHIEUH (ᅙ) and JONGSEONG YEORINHIEUH (ᇹ)
        elif "YEORINHIEUH" in character_name:
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
    if jamo_name in _JAMO_REVERSE_LOOKUP.keys():
        return _JAMO_REVERSE_LOOKUP[jamo_name]
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


def decompose_jamo(compound):
    """Return a tuple of jamo character constituents of a compound.
    Note: Non-compound characters are echoed back.

    WARNING: Archaic jamo compounds will raise NotImplementedError.
    """
    if len(compound) != 1:
        raise TypeError("decompose_jamo() expects a single character,",
                        "but received", type(compound), "length",
                        len(compound))
    if compound not in JAMO_COMPOUNDS:
        # Strict version:
        # raise TypeError("decompose_jamo() expects a compound jamo,",
        #                 "but received", compound)
        return compound
    if compound in JAMO_COMPOUNDS_ARCHAIC:
        raise NotImplementedError
    if is_jamo(compound) and not is_jamo_modern(compound):
        raise NotImplementedError
    return JAMO_COMPOUNDS_MODERN_DICTIONARY.get(compound, compound)


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
