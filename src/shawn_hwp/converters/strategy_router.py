"""Direction-aware conversion routing."""


def choose_route(source_format: str, target_format: str) -> str:
    return f"{source_format.lower()}-to-{target_format.lower()}"
