"""Quality scoring helpers."""

WEIGHTS = {
    "text": 25,
    "structure": 20,
    "table": 15,
    "image_caption": 10,
    "footnote_numbering": 10,
    "submission": 10,
    "roundtrip": 10,
}


def total_weight() -> int:
    return sum(WEIGHTS.values())
