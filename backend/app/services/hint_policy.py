MAX_HINTS = 3

HINTS = {
    "history": [
        "Think about what information is still missing.",
        "Focus on the onset and progression of symptoms.",
        "Review the timeline and associated symptoms.",
    ],
    "physical_exam": [
        "Consider which examination is relevant.",
        "Focus on findings that distinguish possibilities.",
        "Review the examination findings systematically.",
    ],
    "investigations": [
        "Think about what additional evidence is needed.",
        "Choose investigations relevant to your hypothesis.",
        "Compare available results with your differential.",
    ],
    "diagnosis": [
        "Review the evidence collected so far.",
        "Compare your main differential diagnoses.",
        "Identify the findings supporting each possibility.",
    ],
}


def get_hint(mode: str, stage: str, hints_used: int):
    if mode not in ("training", "assessment"):
        raise ValueError("Invalid session mode")

    if stage not in HINTS:
        raise ValueError("Invalid session stage")

    if not isinstance(hints_used, int) or hints_used < 0:
        raise ValueError("Invalid hints_used value")

    if mode == "assessment":
        return {
            "allowed": False,
            "reason": "Hints are disabled in Assessment Mode"
        }

    if hints_used >= MAX_HINTS:
        return {
            "allowed": False,
            "reason": "Maximum hints reached"
        }

    level = hints_used + 1

    return {
        "allowed": True,
        "hint_level": level,
        "hint": HINTS[stage][level - 1],
        "remaining_hints": MAX_HINTS - level
    }