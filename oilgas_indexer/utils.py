import re
from bs4 import BeautifulSoup

WHITESPACE_RE = re.compile(r"\s+")

def clean_text(raw: str) -> str:
    """Clean extracted text for readability."""
    if not raw:
        return ""

    # ---Step 1: Remove HTML structure---    

    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg", "meta", "link"]):
        tag.decompose()

    # --- Step 2: Extract visible text lines ---
        
    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # --- Filter out junk lines ---
    cleaned_lines = []
    for line in lines:
        lower = line.lower()
        if any(phrase in lower for phrase in [
            "cookie", "subscribe", "privacy policy", "terms of use",
            "follow us", "sign up", "newsletter", "contact us",
            "copyright", "all rights reserved", "advertisement", "back to top"



        ]):
            continue

        # skip menu/nav items like “Home / About / Contact”
        if len(line.split()) <=2 and "/" in line:
            continue
        # skip generic short junk
        if len(line.split()) <=2:
            continue
        cleaned_lines.append(line)
        
    # --- Step 4: Join and normalize whitespace ---
    text =" ".join(cleaned_lines)             
    text = WHITESPACE_RE.sub(" ", text)
    text = re.sub(r"\s*([,.;:!?])\s*", r"\1 ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    text = text.strip()

    return text
