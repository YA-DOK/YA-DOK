"""Conservative language-level numeric normalization; no clinical constants.

This provides a defensive check, NOT full semantic entailment. It recognizes
numerals and common written cardinals; unrecognized expressions still need
human-reviewed golden tests and conservative model prompts.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_TRANSLATE = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_EN_UNITS = dict(zip(
    ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"),
    range(20),
))
_EN_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
            "seventy": 70, "eighty": 80, "ninety": 90}
_AR_UNITS = {
    "صفر": 0, "واحد": 1, "واحدة": 1, "اتنين": 2, "اثنين": 2, "اثنان": 2,
    "تلات": 3, "تلاتة": 3, "ثلاث": 3, "ثلاثة": 3, "اربع": 4, "اربعة": 4,
    "خمس": 5, "خمسة": 5, "ست": 6, "ستة": 6, "سبع": 7, "سبعة": 7,
    "تمان": 8, "تمانية": 8, "ثمانية": 8, "تسع": 9, "تسعة": 9,
    "عشر": 10, "عشرة": 10, "حداشر": 11, "احداشر": 11, "اتناشر": 12,
    "تناشر": 12, "اثنا عشر": 12, "تلاتاشر": 13,
    "اربعتاشر": 14, "خمستاشر": 15, "ستاشر": 16, "سبعتاشر": 17,
    "تمنتاشر": 18, "تسعتاشر": 19, "عشرين": 20,
}
# Avoid parsing 'one' inside another word. A missing unit is intentionally
# tolerated, because clinical questions can ask about any quantity.
_NUM = re.compile(r"(?<!\w)\d+(?:[.,]\d+)?(?!\w)")
_WORD = re.compile(r"(?<!\w)[\w-]+(?!\w)", re.UNICODE)


def _strip_arabic(word: str) -> str:
    return (word.casefold().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
            .replace("ى", "ي"))


def explicit_numbers(text: str) -> set[str]:
    text = text.translate(_TRANSLATE).replace("٫", ".")
    values = set()
    for token in _NUM.findall(text):
        try:
            numeric = Decimal(token.replace(",", "."))
            values.add(format(numeric.normalize(), "f"))
        except InvalidOperation:
            # Fail closed on unparseable numeric formats.
            values.add(token)

    words = [_strip_arabic(w) for w in _WORD.findall(text.replace("-", " "))]
    for i, word in enumerate(words):
        if word in _EN_UNITS:
            values.add(str(_EN_UNITS[word]))
        elif word in _EN_TENS:
            value = _EN_TENS[word]
            if i+1 < len(words) and words[i+1] in _EN_UNITS and _EN_UNITS[words[i+1]] < 10:
                value += _EN_UNITS[words[i+1]]
            values.add(str(value))
        elif word in _AR_UNITS:
            values.add(str(_AR_UNITS[word]))
        # English words 'two hundred' -> allow derived 200, while retaining 2;
        # this conservative set may reject some valid responses and fail closed.
        if word in _EN_UNITS and i + 1 < len(words) and words[i+1] == "hundred":
            values.add(str(100 * _EN_UNITS[word]))
    return values


def numbers_grounded(reply: str, allowed_text: str) -> bool:
    """If reply includes explicit numbers, all must appear in supporting facts.

    Does NOT verify the relationship between the number and the symptom or
    convert all natural-language quantities in every dialect.
    """
    return explicit_numbers(reply).issubset(explicit_numbers(allowed_text))
