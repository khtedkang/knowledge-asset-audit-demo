"""Synthetic placeholder showing an interface, with no network access."""

def is_http_url(value: str) -> bool:
    return value.startswith(("https://", "http://"))
