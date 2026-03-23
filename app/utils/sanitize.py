import bleach

ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'a', 'p', 'ul', 'ol', 'li', 'br']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title']}

# For XSS (CWE-79)
def sanitize_html(html: str) -> str:
    if not isinstance(html, str):
        html = str(html)
    # Disallowed tags stripped.
    cleaned = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)   
    return cleaned
