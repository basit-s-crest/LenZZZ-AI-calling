import re

E164_RE = re.compile(r"^\+[1-9]\d{6,14}$")


def is_e164(number: str) -> bool:
    return bool(E164_RE.match(number))


def mask_number(number: str) -> str:
    """+919876543210 -> +91*******3210  (keep phone numbers out of logs)."""
    if len(number) <= 7:
        return "*" * len(number)
    return number[:3] + "*" * (len(number) - 7) + number[-4:]
