"""Domain constants and constraint value sets.

These value sets are derived from the ceramics application models and are used
for CHECK constraints. The application may still accept NULL values; empty
strings are kept because the legacy schema allows them.
"""

from __future__ import annotations

LAYER_TYPE_VALUES = ("механичен", "контекст", "")

COLOR_VALUES = (
    "бял",
    "жълт",
    "охра",
    "червен",
    "сив",
    "тъмносив",
    "кафяв",
    "светлокафяв",
    "тъмнокафяв",
    "черен",
    "",
)

FRAGMENTTYPE_VALUES = ("1", "2", "")
TECHNOLOGY_VALUES = ("1", "2", "2А", "2Б", "")
BAKING_VALUES = ("Р", "Н", "")
FRACT_VALUES = ("1", "2", "3", "")
COVERING_VALUES = ("да", "не", "Ф1", "Ф2", "", "Б", "Г")
INCLUDESCONC_VALUES = ("+", "-", "")
INCLUDESSIZE_VALUES = ("М", "С", "Г", "")
SURFACE_VALUES = ("А", "Б", "В", "В1", "В2", "Г", "")
ONEPOT_VALUES = ("да", "не", "")
PIECETYPE_VALUES = (
    "устие",
    "стена",
    "дръжка",
    "дъно",
    "профил",
    "чучур",
    "дъно+дръжка",
    "профил+дръжка",
    "устие+дръжка",
    "стена+дръжка",
    "псевдочучур",
    "плавен прелом",
    "биконичност",
    "двоен съд",
    "цял съд",
)
WALLTHICKNESS_VALUES = ("М", "С", "Г", "")
HANDLESIZE_VALUES = ("М", "С", "Г", "")
DISHSIZE_VALUES = ("М", "С", "Г", "")
BOTTOMTYPE_VALUES = ("А", "Б", "В", "А1", "А2", "Б1", "Б2", "В1", "В2", "")
OUTLINE_VALUES = ("1", "2", "3", "")

INCLUDETYPE_VALUES = ("антропогенен", "естествен", "")
INCLUDESIZE_VALUES = ("малки", "средни", "големи", "")
INCLUDECONC_VALUES = ("ниска", "средна", "висока", "")

PRIMARY_ORN_VALUES = ("А", "В", "Д", "И", "К", "Н", "П", "Р", "Ф", "Ц", "Щ", "")
SECONDARY_ORN_VALUES = (
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
    "XI",
    "XII",
    "XIII",
    "XIV",
    "XV",
    "XVI",
    "XVII",
    "",
)
TERTIARY_ORN_VALUES = (
    "А",
    "Б",
    "В",
    "Г",
    "Д",
    "Е",
    "Ж",
    "З",
    "И",
    "К",
    "Л",
    "М",
    "П",
    "А1",
    "А2",
    "Б1",
    "Б2",
    "",
)

USER_ROLE_VALUES = ("admin", "user")
