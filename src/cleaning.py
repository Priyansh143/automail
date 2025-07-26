import re
import html

def clean_email_body(text: str) -> str:
    if not text:
        return ""

    # Decode HTML entities
    text = html.unescape(text)

    # Remove zero-width characters, multiple &nbsp;, etc.
    text = re.sub(r'[\u200b\u200c\u200d\u2060\uFEFF]', '', text)
    text = re.sub(r'\s+(&nbsp;|\xa0)+', ' ', text, flags=re.IGNORECASE)
    text = text.replace(u'\xa0', ' ')

    # Collapse excessive whitespace
    text = re.sub(r'\s+', ' ', text)

    # Strip unwanted trailing/leading junk
    return text.strip()
